"""A simple Telegram bot that listens to MQTT messages from Teslamate
and sends them to a Telegram chat."""

import asyncio
import contextlib
import functools
import html
import logging
import os
import signal
import threading
import time
from collections import namedtuple

import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

##############################################################################

# Default values
CAR_ID_DEFAULT = 1
MQTT_BROKER_HOST_DEFAULT = "127.0.0.1"
MQTT_BROKER_PORT_DEFAULT = 1883
MQTT_BROKER_KEEPALIVE = 60
MQTT_BROKER_USERNAME_DEFAULT = ""
MQTT_BROKER_PASSWORD_DEFAULT = ""
MQTT_NAMESPACE_DEFAULT = ""

# The only payloads TeslaMate publishes on the availability topic. Matching
# strictly keeps damaged input from being read as "no update available".
AVAILABILITY_PAYLOADS = {"true": True, "false": False}

# Ctrl+C sends the first, `docker stop` and systemd send the second
STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)

# How long the loop waits between two checks
POLL_INTERVAL_SECONDS = 30
# How long a failed start waits before ending, so a restart policy backs off
ERROR_BACKOFF_SECONDS = 120
# How long an announced update may stay without a version before it is reported
# without one. This only bridges the gap between two MQTT messages, so it is
# much shorter than the poll interval and deliberately a separate figure.
VERSION_GRACE_PERIOD_SECONDS = 5

# Environment variables
TELEGRAM_BOT_API_KEY = "TELEGRAM_BOT_API_KEY"
TELEGRAM_BOT_CHAT_ID = "TELEGRAM_BOT_CHAT_ID"
MQTT_BROKER_USERNAME = "MQTT_BROKER_USERNAME"
MQTT_BROKER_PASSWORD = "MQTT_BROKER_PASSWORD"
MQTT_BROKER_HOST = "MQTT_BROKER_HOST"
MQTT_BROKER_PORT = "MQTT_BROKER_PORT"
MQTT_NAMESPACE = "MQTT_NAMESPACE"
CAR_ID = "CAR_ID"

##############################################################################

# Logging
# Configure the logging module to output info level logs and above
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Module logger, attached to the root handler configured above
logger = logging.getLogger(__name__)

# What check_state_and_send_messages found to be due: which episode, and the
# version if one is known by now
PendingNotification = namedtuple("PendingNotification", ["episode", "version"])

# An availability episode: which one it is, and when it began. The two belong
# together - the number identifies the notification, the start time bounds how
# long it waits for a version.
Episode = namedtuple("Episode", ["number", "started_at"])


class State:
    """A class to hold the state of the application.

    Created in main() and handed to the MQTT client as its user data, so the
    callbacks receive it as an argument instead of reaching for a module
    global.

    Written from paho's network thread and read from the asyncio side, so the
    fields are private and every access goes through a method holding the
    lock. The lock makes each of those methods an atomic local operation; it
    says nothing about how the two MQTT topics relate to each other, since
    availability and version arrive as separate messages.

    The notification belongs to an availability episode, not to a version:
    update_available is the signal that matters, the version is optional
    extra information that must never block the message indefinitely. Every
    transition from false to true starts a new episode and earns exactly one
    message, no matter how often true is repeated within it.

    Acknowledging names the episode that was sent. Sending is awaited and the
    state can move on while it is in flight - acknowledging "the current
    state" would then swallow an episode that started in the meantime.
    """

    UNKNOWN_VERSIONS = ("unknown", "")

    def __init__(self, clock=time.monotonic):
        self._lock = threading.Lock()
        self._clock = clock
        # None until the first message says so: a retained "false" at startup
        # is then not mistaken for an update that just went away.
        self._update_available = None
        self._update_version = "unknown"
        self._episode = Episode(number=0, started_at=None)  # 0 means none yet
        self._notified_episode = 0
        self._connection_failure = None

    def record_version(self, version):
        """Store the version announced by TeslaMate."""
        with self._lock:
            self._update_version = version

    def record_availability(self, available):
        """Store whether an update is available.

        Going from false to true opens a new episode. Repeated true changes
        nothing, so a retained message or a reconnect does not notify twice.

        Actually losing availability forgets the version: it described the
        update that is now gone, and reusing it would announce the next
        episode with the previous version. A version published after that
        point still belongs to the coming episode and is kept - which is why
        only the transition clears, not every repeated false.
        """
        with self._lock:
            if available and not self._update_available:
                self._episode = Episode(
                    number=self._episode.number + 1, started_at=self._clock()
                )
            elif self._update_available and not available:
                self._update_version = "unknown"
            self._update_available = available

    def current_version(self):
        """Return the version currently announced, whether notified or not."""
        with self._lock:
            return self._update_version

    def pending_notification(self, grace_period):
        """Return the notification that is due, or None.

        A due episode without a version is held back for the grace period, so
        a version arriving shortly after the availability still makes it into
        the message. Once that time is up the message goes out without one.
        """
        with self._lock:
            if not self._update_available:
                return None
            if self._episode.number == self._notified_episode:
                return None

            version = self._update_version
            if version in self.UNKNOWN_VERSIONS:
                if self._clock() - self._episode.started_at < grace_period:
                    return None
                version = None

            return PendingNotification(episode=self._episode.number, version=version)

    def mark_notified(self, episode):
        """Acknowledge exactly the episode that was sent, not the current one."""
        with self._lock:
            self._notified_episode = episode

    def record_connection_failure(self, reason):
        """Report that the broker rejected the connection.

        The callback runs in paho's network thread, where exiting would only
        end that thread and leave the asyncio loop polling a state nobody
        updates any more. main() picks the reason up and stops the bot.
        """
        with self._lock:
            self._connection_failure = reason

    def connection_failure(self):
        """Return why the broker rejected the connection, or None."""
        with self._lock:
            return self._connection_failure


def get_env_variable(var_name, default_value=None):
    """Get the environment variable or return a default value

    Only whether the variable is set is logged, never its content: two of
    them carry the Telegram token and the MQTT password, and debug logs end
    up in files, `docker logs` and forwarders. The values that are safe to
    see - broker, port, namespace, car - are logged where they are used.
    """
    logger.debug("Getting environment variable %s", var_name)
    raw_value = os.getenv(var_name)
    var_value = raw_value if raw_value is not None else default_value
    logger.debug(
        "Environment variable %s is %s",
        var_name,
        "set" if raw_value is not None else "not set, using the default",
    )
    if var_value is None and var_name in [TELEGRAM_BOT_API_KEY, TELEGRAM_BOT_CHAT_ID]:
        error_message_get_env_variable = (
            f"Error: Please set the environment variable {var_name} and try again."
        )
        raise OSError(error_message_get_env_variable)
    return var_value


# MQTT topics
try:
    car_id = int(get_env_variable(CAR_ID, CAR_ID_DEFAULT))
except ValueError as value_error_car_id:
    ERROR_MESSAGE_CAR_ID = (
        f"Error: Please set the environment variable {CAR_ID} "
        f"to a valid number and try again."
    )
    raise OSError(ERROR_MESSAGE_CAR_ID) from value_error_car_id


namespace = get_env_variable(MQTT_NAMESPACE, MQTT_NAMESPACE_DEFAULT)
if namespace:
    logger.info("Using MQTT namespace: %s", namespace)
    TESLAMATE_MQTT_TOPIC_BASE = f"teslamate/{namespace}/cars/{car_id}/"
else:
    TESLAMATE_MQTT_TOPIC_BASE = f"teslamate/cars/{car_id}/"

TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE = TESLAMATE_MQTT_TOPIC_BASE + "update_available"
TESLAMATE_MQTT_TOPIC_UPDATE_VERSION = TESLAMATE_MQTT_TOPIC_BASE + "update_version"


def on_connect(client, userdata, flags, reason_code, properties=None):  # noqa: ARG001  # pylint: disable=unused-argument
    """The callback for when the client receives a CONNACK response from the server.

    Signature is fixed by paho-mqtt; not every argument is used. userdata is
    the State instance handed to the client in setup_mqtt_client.

    A rejected connection is reported through the state rather than ended
    here: this runs in paho's network thread, where exiting would end that
    thread alone and leave main() polling forever without MQTT.
    """
    state = userdata
    logger.debug("Connected with result code: %s", reason_code)
    if reason_code != 0:
        logger.error("Connection to the MQTT broker failed: %s", reason_code)
        state.record_connection_failure(reason_code)
        return

    logger.info("Connected successfully to MQTT broker")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    logger.info("Subscribing to MQTT topics:")

    client.subscribe(TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE)
    logger.info("Subscribed to MQTT topic: %s", TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE)

    client.subscribe(TESLAMATE_MQTT_TOPIC_UPDATE_VERSION)
    logger.info("Subscribed to MQTT topic: %s", TESLAMATE_MQTT_TOPIC_UPDATE_VERSION)

    logger.info("Subscribed to all MQTT topics.")

    logger.info("Waiting for MQTT messages...")


def on_message(client, userdata, msg):  # noqa: ARG001  # pylint: disable=unused-argument
    """The callback for when a PUBLISH message is received from the server.

    Signature is fixed by paho-mqtt; not every argument is used. userdata is
    the State instance handed to the client in setup_mqtt_client.
    """
    state = userdata
    try:
        payload = msg.payload.decode()
    except UnicodeDecodeError:
        # Damaged bytes must not escape into paho's network thread, where an
        # exception ends the loop that feeds this bot.
        logger.warning(
            "Ignoring undecodable payload of %s bytes on %s",
            len(msg.payload),
            msg.topic,
        )
        return

    logger.debug("Received message: %s %s", msg.topic, payload)

    if msg.topic == TESLAMATE_MQTT_TOPIC_UPDATE_VERSION:
        state.record_version(payload)
        logger.info("Update to version %s available.", payload)

    if msg.topic == TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE:
        if payload not in AVAILABILITY_PAYLOADS:
            # Anything else is damaged input. Reading it as "false" would end
            # the episode and discard the version, so it is dropped instead.
            logger.warning("Ignoring unexpected payload on %s: %r", msg.topic, payload)
            return

        available = AVAILABILITY_PAYLOADS[payload]
        state.record_availability(available)
        if available:
            logger.info(
                "A new SW update to version: %s for your Tesla is available!",
                state.current_version(),
            )
        else:
            logger.debug("No SW update available.")


def setup_mqtt_client(state):
    """Setup the MQTT client

    The state is registered as the client's user data, so paho hands it to the
    callbacks on every message.
    """
    logger.info("Setting up the MQTT client...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=state)
    client.on_connect = on_connect
    client.on_message = on_message

    username = get_env_variable(MQTT_BROKER_USERNAME, MQTT_BROKER_USERNAME_DEFAULT)
    password = get_env_variable(MQTT_BROKER_PASSWORD, MQTT_BROKER_PASSWORD_DEFAULT)
    client.username_pw_set(username, password)

    host = get_env_variable(MQTT_BROKER_HOST, MQTT_BROKER_HOST_DEFAULT)
    try:
        port = int(get_env_variable(MQTT_BROKER_PORT, MQTT_BROKER_PORT_DEFAULT))
    except ValueError as value_error_mqtt_broker_port:
        error_message_mqtt_broker_port = (
            f"Error: Please set the environment variable {MQTT_BROKER_PORT} "
            f"to a valid number and try again."
        )
        raise OSError(error_message_mqtt_broker_port) from value_error_mqtt_broker_port
    logger.info("Connect to MQTT broker at %s:%s", host, port)
    client.connect(host, port, MQTT_BROKER_KEEPALIVE)

    return client


def setup_telegram_bot():
    """Setup the Telegram bot"""
    logger.info("Setting up the Telegram bot...")
    bot = Bot(get_env_variable(TELEGRAM_BOT_API_KEY))
    try:
        chat_id = int(get_env_variable(TELEGRAM_BOT_CHAT_ID))
    except ValueError as value_error_chat_id:
        error_message_chat_id = (
            f"Error: Please set the environment variable {TELEGRAM_BOT_CHAT_ID} "
            f"to a valid number and try again."
        )
        raise OSError(error_message_chat_id) from value_error_chat_id

    logger.info("Connected to Telegram bot successfully.")
    return bot, chat_id


async def check_state_and_send_messages(bot, chat_id, state):
    """Check the state and send messages if necessary"""
    logger.debug("Checking state and sending messages...")

    notification = state.pending_notification(VERSION_GRACE_PERIOD_SECONDS)
    if notification is None:
        return

    if notification.version is None:
        logger.info("A new SW update for your Tesla is available!")
        message_text = (
            "<b>SW Update 🎁</b>\nA new SW update for your Tesla is available!"
        )
    else:
        logger.info(
            "A new SW update to version: %s for your Tesla is available!",
            notification.version,
        )
        # The version comes from MQTT and goes into a message Telegram parses
        # as HTML, where a bare &, < or > is a parse error - and that error
        # would arrive as the TelegramError that ends the bot.
        message_text = (
            "<b>"
            "SW Update 🎁"
            "</b>\n"
            "A new SW update to version: "
            + html.escape(notification.version)
            + " for your Tesla is available!"
        )

    await send_telegram_message_to_chat_id(bot, chat_id, message_text)

    # Acknowledge the episode that was just sent. The state may have moved on
    # during the await; an episode that started in the meantime then stays
    # pending instead of being marked as reported.
    state.mark_notified(notification.episode)
    logger.debug("Episode %s acknowledged as notified.", notification.episode)


async def send_telegram_message_to_chat_id(bot, chat_id, message_text_to_send):
    """Send a message to a chat ID"""
    logger.debug("Sending message.")
    await bot.send_message(
        chat_id,
        text=message_text_to_send,
        parse_mode=ParseMode.HTML,
    )
    logger.debug("Message sent.")


def request_stop(stop_requested, signal_number):
    """Ask the main loop to finish, from a signal handler."""
    logger.info("Received %s, shutting down.", signal.Signals(signal_number).name)
    stop_requested.set()


@contextlib.contextmanager
def stop_signals_handled(stop_requested):
    """Route SIGINT and SIGTERM to the stop event for the whole run.

    Installed around everything, not just the polling loop: setup, the
    greeting, the backoff after a failed start and the shutdown itself all
    take time, and a stop arriving in any of them must be honoured rather
    than killing the process where it stands.

    Unix only: loop.add_signal_handler is not implemented on Windows, which
    the project does not target - it ships as a Linux container and as a
    NixOS service.
    """
    running_loop = asyncio.get_running_loop()
    previous_handlers = {number: signal.getsignal(number) for number in STOP_SIGNALS}
    for number in STOP_SIGNALS:
        running_loop.add_signal_handler(
            number, functools.partial(request_stop, stop_requested, number)
        )
    try:
        yield
    finally:
        for number in STOP_SIGNALS:
            # This resets the disposition to the default, so whatever the
            # process had before is put back afterwards.
            running_loop.remove_signal_handler(number)
            if previous_handlers[number] is not None:
                signal.signal(number, previous_handlers[number])


async def wait_for_stop(stop_requested, timeout):
    """Wait for a stop signal, giving up after the timeout."""
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop_requested.wait(), timeout)


async def run_until_stopped(bot, chat_id, state, stop_requested):
    """Poll the state until the stop event is set.

    The event is owned by main(), which arms it for the whole lifecycle; here
    it only ends the wait between two rounds.
    """
    while not stop_requested.is_set():
        # The connect callback cannot end the bot itself, it runs in paho's
        # thread. Without this the loop would keep polling a state that
        # nobody updates any more.
        connection_failure = state.connection_failure()
        if connection_failure is not None:
            raise OSError(
                f"Error: The MQTT broker rejected the connection: {connection_failure}"
            )

        await check_state_and_send_messages(bot, chat_id, state)

        logger.debug("Sleeping for %s seconds.", POLL_INTERVAL_SECONDS)
        await wait_for_stop(stop_requested, POLL_INTERVAL_SECONDS)


async def shut_down(client, bot, chat_id):
    """Release whatever was set up, in the order it has to happen.

    A failure in setup_telegram_bot leaves an already connected MQTT client
    behind, so each part is released on its own terms.
    """
    if client is not None:
        logger.info("Disconnecting from MQTT broker.")
        client.disconnect()
        logger.info("Disconnected from MQTT broker.")
        client.loop_stop()

    logger.info("Exiting the Teslamate Telegram bot.")

    if bot is None:
        return

    stop_message = "<b>Teslamate Telegram Bot stopped. 🛑</b>\n "
    try:
        await send_telegram_message_to_chat_id(bot, chat_id, stop_message)
    except TelegramError as telegram_error:
        # Telegram being unreachable is what brings the bot down in the first
        # place. Saying goodbye over the same channel then fails too, and an
        # exception raised in here would replace the one that caused the
        # shutdown, hiding the actual cause.
        logger.error("Could not send the stop message: %s", telegram_error)
    finally:
        # Releasing the resources must not depend on the goodbye getting
        # through. shutdown() frees the local request objects; close() would
        # be the API call for moving a bot between servers, which Telegram
        # answers with 429 in the first ten minutes after a start - every
        # restart of a short-lived container.
        try:
            await bot.shutdown()
        except TelegramError as telegram_error:
            logger.error("Could not release the bot's resources: %s", telegram_error)


# Main function
async def main():
    """Main function"""
    logger.info("Starting the Teslamate Telegram Bot.")
    state = State()
    stop_requested = asyncio.Event()
    # Bound up front so the shutdown can tell what actually got set up.
    client = None
    bot = None
    chat_id = None
    with stop_signals_handled(stop_requested):
        try:
            client = setup_mqtt_client(state)
            bot, chat_id = setup_telegram_bot()
            start_message = (
                "<b>"
                "Teslamate Telegram Bot started ✅"
                "</b>\n"
                "and will notify as soon as a new SW version is available."
            )
            await send_telegram_message_to_chat_id(bot, chat_id, start_message)

            client.loop_start()
            await run_until_stopped(bot, chat_id, state, stop_requested)
        except OSError as e:
            logger.error(e)
            logger.info(
                "Waiting %s seconds before exiting or restarting, depending on your "
                "restart policy.",
                ERROR_BACKOFF_SECONDS,
            )
            await wait_for_stop(stop_requested, ERROR_BACKOFF_SECONDS)
        finally:
            await shut_down(client, bot, chat_id)


# Entry point
def main_sync():
    """Synchronous entry point for the bot."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
