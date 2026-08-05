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
from dataclasses import dataclass, field

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

# What the process reports back: a failed start has to be distinguishable
# from a requested stop, or a supervisor cannot tell whether to restart
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# How long to wait for the broker to confirm both subscriptions before giving
# up on the start, and how often to look while waiting
MQTT_READY_TIMEOUT_SECONDS = 30
MQTT_READY_POLL_SECONDS = 0.5

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

# httpx logs every request at INFO, including the URL - and the Telegram API
# carries the bot token in the path. At the root level set above that would
# put the token into the log on every message sent. Silencing the logger
# itself also holds when someone raises the root level to DEBUG.
logging.getLogger("httpx").setLevel(logging.WARNING)

# Module logger, attached to the root handler configured above
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PendingNotification:
    """What check_state_and_send_messages found to be due."""

    episode: int
    version: str | None  # None when no version is known by now


@dataclass(frozen=True, slots=True)
class Episode:
    """An availability episode: which one it is, and when it began.

    The two belong together - the number identifies the notification, the
    start time bounds how long it waits for a version.
    """

    number: int
    started_at: float | None


class State:
    """A class to hold the state of the application.

    Created in main() and passed to the MQTT client inside an
    MqttCallbackContext, which paho hands back as user data - so the callbacks
    receive it as an argument instead of reaching for a module global.

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

    "No version known" is a single value inside: None. The empty string and
    the literal "unknown" are normalised away where they enter, so no reader
    has to know about more than one way of saying it.
    """

    # TeslaMate documents update_version as a concrete version number and no
    # sentinel, so these are defensive: an empty retained message, and the
    # placeholder this bot itself used to store.
    UNKNOWN_VERSION_PAYLOADS = ("", "unknown")

    def __init__(self, clock=time.monotonic):
        self._lock = threading.Lock()
        self._clock = clock
        # None until the first message says so: a retained "false" at startup
        # is then not mistaken for an update that just went away.
        self._update_available = None
        self._update_version: str | None = None
        self._episode = Episode(number=0, started_at=None)  # 0 means none yet
        self._notified_episode = 0

    def record_version(self, version: str) -> None:
        """Store the version announced by TeslaMate, normalising the unknowns."""
        with self._lock:
            self._update_version = (
                None if version in self.UNKNOWN_VERSION_PAYLOADS else version
            )

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
                self._update_version = None
            self._update_available = available

    def current_version(self) -> str | None:
        """Return the version currently announced, None if none is known."""
        with self._lock:
            return self._update_version

    def pending_notification(self, grace_period: float) -> PendingNotification | None:
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

            # Only the initial episode carries no start time, and it is ruled
            # out above: availability has been seen, so an episode has begun.
            started_at = self._episode.started_at
            assert started_at is not None

            version = self._update_version
            if version is None and self._clock() - started_at < grace_period:
                return None

            return PendingNotification(episode=self._episode.number, version=version)

    def mark_notified(self, episode):
        """Acknowledge exactly the episode that was sent, not the current one."""
        with self._lock:
            self._notified_episode = episode


class BrokerStatus:
    """How the connection to the MQTT broker is doing.

    Kept apart from State on purpose: that one holds what TeslaMate reports
    about the car, this one holds what the broker reports about the transport.
    The two change for different reasons and are read in different places.

    Written from paho's network thread and read from the asyncio side, so the
    fields are private and every access holds the lock.
    """

    def __init__(self, clock=time.monotonic):
        self._lock = threading.Lock()
        self._clock = clock
        self._connection_failure = None
        self._pending_subscriptions = set()
        self._confirmed_subscriptions = 0
        self._subscription_failure = None
        self._unconfirmed_since = None

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

    def reset_subscriptions(self):
        """Forget what an earlier connection was waiting for.

        A connection that drops between SUBSCRIBE and SUBACK leaves message
        ids behind that will never be answered. Kept, they would make the
        next, successful attempt wait for them and time out.

        The clock starts here, in the moment of the reconnect, rather than
        whenever the polling loop next looks - otherwise the grace would
        stretch by up to one poll interval.
        """
        with self._lock:
            self._pending_subscriptions.clear()
            self._confirmed_subscriptions = 0
            self._unconfirmed_since = self._clock()

    def expect_subscription(self, message_id):
        """Remember a subscribe request that still awaits its SUBACK."""
        with self._lock:
            self._pending_subscriptions.add(message_id)

    def record_subscription_result(self, message_id, reason_codes):
        """Take the broker's answer to one subscribe request.

        A broker may accept the connection and still refuse a subscription,
        an ACL being the usual reason. Without this the bot would look
        healthy and never report anything.
        """
        refused = [code for code in reason_codes if code.is_failure]
        with self._lock:
            self._pending_subscriptions.discard(message_id)
            if refused:
                self._subscription_failure = ", ".join(str(code) for code in refused)
            else:
                self._confirmed_subscriptions += 1
            if self._confirmed_subscriptions > 0 and not self._pending_subscriptions:
                self._unconfirmed_since = None

    def record_subscription_failure(self, reason):
        """Report a subscribe request the client could not even send."""
        with self._lock:
            self._subscription_failure = reason

    def subscription_failure(self):
        """Return why a subscription was refused, or None."""
        with self._lock:
            return self._subscription_failure

    def subscriptions_ready(self):
        """Whether every subscribe request has been confirmed by the broker."""
        with self._lock:
            return self._confirmed_subscriptions > 0 and not self._pending_subscriptions

    def unconfirmed_duration(self):
        """How long the subscriptions have been unconfirmed, None if they are.

        Measured from the reconnect itself, so the answer does not depend on
        how often the caller happens to ask.
        """
        with self._lock:
            if self._unconfirmed_since is None:
                return None
            return self._clock() - self._unconfirmed_since

    def failure(self):
        """Return why the broker connection is unusable, or None.

        One question with one answer: both the refused connection and the
        refused subscription leave the bot unable to hear anything, and every
        caller has to react the same way.
        """
        with self._lock:
            if self._connection_failure is not None:
                return f"the broker rejected the connection: {self._connection_failure}"
            if self._subscription_failure is not None:
                return (
                    f"the broker refused a subscription: {self._subscription_failure}"
                )
            return None


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


@dataclass(frozen=True, slots=True)
class Config:  # pylint: disable=too-many-instance-attributes
    """Everything the bot reads from the environment, read once at startup.

    Taken as a snapshot rather than looked up where needed: the settings then
    cannot change halfway through a run, importing the module has no side
    effects, and a test hands in a Config instead of arranging os.environ.

    The secrets are kept out of repr(), so a config in a traceback or a debug
    line does not carry the Telegram token or the broker password.

    The field count is what the environment offers, not a design decision -
    this holds settings, it does not do anything with them, so the limit on
    instance attributes does not apply.
    """

    car_id: int
    namespace: str
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str = field(repr=False)
    telegram_token: str = field(repr=False)
    telegram_chat_id: int

    @classmethod
    def from_env(cls):
        """Read and validate the environment, raising OSError on bad input."""
        namespace = get_env_variable(MQTT_NAMESPACE, MQTT_NAMESPACE_DEFAULT)
        if namespace:
            logger.info("Using MQTT namespace: %s", namespace)

        return cls(
            car_id=cls._as_number(CAR_ID, get_env_variable(CAR_ID, CAR_ID_DEFAULT)),
            namespace=namespace,
            mqtt_host=get_env_variable(MQTT_BROKER_HOST, MQTT_BROKER_HOST_DEFAULT),
            mqtt_port=cls._as_number(
                MQTT_BROKER_PORT,
                get_env_variable(MQTT_BROKER_PORT, MQTT_BROKER_PORT_DEFAULT),
            ),
            mqtt_username=get_env_variable(
                MQTT_BROKER_USERNAME, MQTT_BROKER_USERNAME_DEFAULT
            ),
            mqtt_password=get_env_variable(
                MQTT_BROKER_PASSWORD, MQTT_BROKER_PASSWORD_DEFAULT
            ),
            telegram_token=get_env_variable(TELEGRAM_BOT_API_KEY),
            telegram_chat_id=cls._as_number(
                TELEGRAM_BOT_CHAT_ID, get_env_variable(TELEGRAM_BOT_CHAT_ID)
            ),
        )

    @staticmethod
    def _as_number(var_name, value):
        """Turn a setting into a number, or say which one is unusable."""
        try:
            return int(value)
        except ValueError as value_error:
            error_message = (
                f"Error: Please set the environment variable {var_name} "
                f"to a valid number and try again."
            )
            raise OSError(error_message) from value_error

    @property
    def topic_base(self) -> str:
        """The prefix all topics of this car share."""
        if self.namespace:
            return f"teslamate/{self.namespace}/cars/{self.car_id}/"
        return f"teslamate/cars/{self.car_id}/"

    @property
    def update_available_topic(self) -> str:
        """Derived, never stored: it cannot drift from car id and namespace."""
        return self.topic_base + "update_available"

    @property
    def update_version_topic(self) -> str:
        """Derived, never stored: it cannot drift from car id and namespace."""
        return self.topic_base + "update_version"


@dataclass(frozen=True, slots=True)
class MqttCallbackContext:
    """What paho hands back to the callbacks as user data.

    Both the settings and the shared state travel the same way, through the
    argument paho provides for exactly this - no module globals involved, so
    two clients with different car ids cannot leak into each other.
    """

    config: Config
    state: State
    status: BrokerStatus


def on_connect(client, userdata, flags, reason_code, properties=None):  # noqa: ARG001  # pylint: disable=unused-argument
    """The callback for when the client receives a CONNACK response from the server.

    Signature is fixed by paho-mqtt; not every argument is used. userdata is
    the MqttCallbackContext handed to the client in setup_mqtt_client.

    A rejected connection is reported through the state rather than ended
    here: this runs in paho's network thread, where exiting would end that
    thread alone and leave main() polling forever without MQTT.
    """
    context = userdata
    logger.debug("Connected with result code: %s", reason_code)
    if reason_code != 0:
        logger.error("Connection to the MQTT broker failed: %s", reason_code)
        context.status.record_connection_failure(reason_code)
        return

    logger.info("Connected successfully to MQTT broker")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed - starting over, because
    # whatever the dropped connection was still waiting for will never come.
    context.status.reset_subscriptions()
    logger.info("Subscribing to MQTT topics:")

    for topic in (
        context.config.update_available_topic,
        context.config.update_version_topic,
    ):
        result, message_id = client.subscribe(topic)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Could not request a subscription to %s: %s", topic, result)
            context.status.record_subscription_failure(
                f"the subscribe request for {topic} failed with {result}"
            )
            return
        # Requested, not granted: the broker answers with a SUBACK, and only
        # on_subscribe knows whether it accepted.
        context.status.expect_subscription(message_id)
        logger.info("Requested subscription to MQTT topic: %s", topic)


def on_subscribe(client, userdata, mid, reason_code_list, properties=None):  # noqa: ARG001  # pylint: disable=unused-argument
    """The callback for the broker's answer to a subscribe request.

    Signature is fixed by paho-mqtt; not every argument is used. A broker can
    accept the connection and still refuse a subscription - an ACL that
    forbids the topic is the usual reason - and without looking here the bot
    would wait for messages that are never going to arrive.
    """
    context = userdata
    refused = [code for code in reason_code_list if code.is_failure]
    if refused:
        logger.error("The MQTT broker refused a subscription: %s", refused)
    else:
        logger.info("Subscription confirmed by the MQTT broker.")
    context.status.record_subscription_result(mid, reason_code_list)


def on_message(client, userdata, msg):  # noqa: ARG001  # pylint: disable=unused-argument
    """The callback for when a PUBLISH message is received from the server.

    Signature is fixed by paho-mqtt; not every argument is used. userdata is
    the MqttCallbackContext handed to the client in setup_mqtt_client.
    """
    context = userdata
    state = context.state
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

    if msg.topic == context.config.update_version_topic:
        state.record_version(payload)
        logger.info("Update to version %s available.", payload)

    if msg.topic == context.config.update_available_topic:
        if payload not in AVAILABILITY_PAYLOADS:
            # Anything else is damaged input. Reading it as "false" would end
            # the episode and discard the version, so it is dropped instead.
            logger.warning("Ignoring unexpected payload on %s: %r", msg.topic, payload)
            return

        available = AVAILABILITY_PAYLOADS[payload]
        state.record_availability(available)
        if available:
            # "unknown" only as a display value here; inside, None is the one
            # way of saying that no version is known.
            logger.info(
                "A new SW update to version: %s for your Tesla is available!",
                state.current_version() or "unknown",
            )
        else:
            logger.debug("No SW update available.")


def setup_mqtt_client(context):
    """Setup the MQTT client

    The context is registered as the client's user data, so paho hands the
    settings and the shared state to the callbacks on every message.
    """
    logger.info("Setting up the MQTT client...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=context)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    config = context.config
    client.username_pw_set(config.mqtt_username, config.mqtt_password)

    logger.info("Connect to MQTT broker at %s:%s", config.mqtt_host, config.mqtt_port)
    client.connect(config.mqtt_host, config.mqtt_port, MQTT_BROKER_KEEPALIVE)

    return client


def setup_telegram_bot(config):
    """Setup the Telegram bot"""
    logger.info("Setting up the Telegram bot...")
    bot = Bot(config.telegram_token)
    logger.info("Connected to Telegram bot successfully.")
    return bot


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


async def wait_until_subscribed(status, stop_requested, clock=time.monotonic):
    """Block until the broker has confirmed every subscription.

    Reporting a successful start before this would be a guess: the connect
    callback only asks, and a broker that accepts the connection can still
    refuse the topics.

    Returns whether the subscriptions were confirmed. False means a stop was
    requested while waiting - the caller must not announce a running bot then,
    because nothing has confirmed that it hears anything.
    """
    logger.info("Waiting for the MQTT broker to confirm the subscriptions...")
    deadline = clock() + MQTT_READY_TIMEOUT_SECONDS

    while not stop_requested.is_set():
        failure = status.failure()
        if failure is not None:
            raise OSError(f"Error: Cannot listen for updates, {failure}.")

        if status.subscriptions_ready():
            logger.info("Subscribed to all MQTT topics.")
            logger.info("Waiting for MQTT messages...")
            return True

        if clock() >= deadline:
            raise OSError(
                f"Error: The MQTT broker did not confirm the subscriptions within "
                f"{MQTT_READY_TIMEOUT_SECONDS} seconds."
            )

        await wait_for_stop(stop_requested, MQTT_READY_POLL_SECONDS)

    logger.info("Stopped before the subscriptions were confirmed.")
    return False


async def run_until_stopped(bot, chat_id, context, stop_requested):
    """Poll the state until the stop event is set.

    The event is owned by main(), which arms it for the whole lifecycle; here
    it only ends the wait between two rounds.

    A reconnect starts the subscriptions over, so the bot can fall silent
    again long after a successful start - by a refusal, or by a broker that
    simply never answers. Both end the run, the second one after the same
    grace the start allows. How long that has been going on is BrokerStatus's
    answer, timed from the reconnect rather than from this loop noticing it.
    """
    while not stop_requested.is_set():
        # The callbacks cannot end the bot themselves, they run in paho's
        # thread. Without this the loop would keep polling a state that
        # nobody updates any more.
        failure = context.status.failure()
        if failure is not None:
            raise OSError(f"Error: Lost the updates, {failure}.")

        unconfirmed_for = context.status.unconfirmed_duration()
        if (
            unconfirmed_for is not None
            and unconfirmed_for >= MQTT_READY_TIMEOUT_SECONDS
        ):
            raise OSError(
                f"Error: The MQTT broker stopped confirming the subscriptions "
                f"for more than {MQTT_READY_TIMEOUT_SECONDS} seconds."
            )

        await check_state_and_send_messages(bot, chat_id, context.state)

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
    """Run the bot, returning the exit status.

    A failed start reports failure, so a supervisor configured to restart on
    failure - as the NixOS service is - actually restarts after a broker
    outage instead of staying down for good.
    """
    logger.info("Starting the Teslamate Telegram Bot.")
    stop_requested = asyncio.Event()
    failed = False
    # Bound up front so the shutdown can tell what actually got set up.
    client = None
    bot = None
    chat_id = None
    with stop_signals_handled(stop_requested):
        try:
            # Read once, here: unusable settings then take the same route as
            # any other startup failure instead of breaking the import.
            context = MqttCallbackContext(
                config=Config.from_env(), state=State(), status=BrokerStatus()
            )
            chat_id = context.config.telegram_chat_id
            client = setup_mqtt_client(context)
            bot = setup_telegram_bot(context.config)

            # Only now can CONNACK and SUBACK be processed, so the start
            # message waits until the broker has actually confirmed both
            # subscriptions - announcing a working bot before that would be a
            # guess.
            client.loop_start()
            if await wait_until_subscribed(context.status, stop_requested):
                start_message = (
                    "<b>"
                    "Teslamate Telegram Bot started ✅"
                    "</b>\n"
                    "and will notify as soon as a new SW version is available."
                )
                await send_telegram_message_to_chat_id(bot, chat_id, start_message)

                await run_until_stopped(bot, chat_id, context, stop_requested)
        except OSError as e:
            logger.error(e)
            logger.info(
                "Waiting %s seconds before exiting or restarting, depending on your "
                "restart policy.",
                ERROR_BACKOFF_SECONDS,
            )
            await wait_for_stop(stop_requested, ERROR_BACKOFF_SECONDS)
            # Being asked to stop during the backoff is a regular shutdown:
            # the operator wanted this, so it is not reported as a failure.
            failed = not stop_requested.is_set()
        finally:
            await shut_down(client, bot, chat_id)

    return EXIT_FAILURE if failed else EXIT_SUCCESS


# Entry point
def main_sync():
    """Synchronous entry point for the bot, exiting with its status."""
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    main_sync()
