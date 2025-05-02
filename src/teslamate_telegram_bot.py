""" A simple Telegram bot that listens to MQTT messages from Teslamate
and sends them to a Telegram chat."""
import os
import sys
import logging
import asyncio
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.constants import ParseMode

##############################################################################

# Default values
CAR_ID_DEFAULT = 1
MQTT_BROKER_HOST_DEFAULT = '127.0.0.1'
MQTT_BROKER_PORT_DEFAULT = 1883
MQTT_BROKER_KEEPALIVE = 60
MQTT_BROKER_USERNAME_DEFAULT = ''
MQTT_BROKER_PASSWORD_DEFAULT = ''
MQTT_NAMESPACE_DEFAULT = ''

# Environment variables
TELEGRAM_BOT_API_KEY = 'TELEGRAM_BOT_API_KEY'
TELEGRAM_BOT_CHAT_ID = 'TELEGRAM_BOT_CHAT_ID'
MQTT_BROKER_USERNAME = 'MQTT_BROKER_USERNAME'
MQTT_BROKER_PASSWORD = 'MQTT_BROKER_PASSWORD'
MQTT_BROKER_HOST = 'MQTT_BROKER_HOST'
MQTT_BROKER_PORT = 'MQTT_BROKER_PORT'
MQTT_NAMESPACE = 'MQTT_NAMESPACE'
CAR_ID = 'CAR_ID'

##############################################################################

# Logging
# Configure the logging module to output info level logs and above
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Global state
class State:
    """ A class to hold the global state of the application."""
    def __init__(self):
        self.update_available = False               # Flag to indicate if an update is available
        self.update_available_message_sent = False  # Flag to indicate if the message has been sent
        self.update_version = "unknown"             # The version of the update


# Global state
state = State()


def get_env_variable(var_name, default_value=None):
    """ Get the environment variable or return a default value"""
    logging.debug("Getting environment variable %s", var_name)
    var_value = os.getenv(var_name, default_value)
    logging.debug("Environment variable %s: %s", var_name, var_value)
    if var_value is None and var_name in [TELEGRAM_BOT_API_KEY, TELEGRAM_BOT_CHAT_ID]:
        error_message_get_env_variable = f"Error: Please set the environment variable {var_name} and try again."
        raise EnvironmentError(error_message_get_env_variable)
    return var_value


# MQTT topics
try:
    car_id = int(get_env_variable(CAR_ID, CAR_ID_DEFAULT))
except ValueError as value_error_car_id:
    ERROR_MESSAGE_CAR_ID = (f"Error: Please set the environment variable {CAR_ID} "
                            f"to a valid number and try again."
                            )
    raise EnvironmentError(ERROR_MESSAGE_CAR_ID) from value_error_car_id


namespace = get_env_variable(MQTT_NAMESPACE, MQTT_NAMESPACE_DEFAULT)
if namespace:
    logging.info("Using MQTT namespace: %s", namespace)
    TESLAMATE_MQTT_TOPIC_BASE = f"teslamate/{namespace}/cars/{car_id}/"
else:
    TESLAMATE_MQTT_TOPIC_BASE = f"teslamate/cars/{car_id}/"

TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE = TESLAMATE_MQTT_TOPIC_BASE + "update_available"
TESLAMATE_MQTT_TOPIC_UPDATE_VERSION = TESLAMATE_MQTT_TOPIC_BASE + "update_version"


def on_connect(client, userdata, flags, reason_code, properties=None):  # pylint: disable=unused-argument
    """ The callback for when the client receives a CONNACK response from the server."""
    logging.debug("Connected with result code: %s", reason_code)
    if reason_code == "Unsupported protocol version":
        logging.error("Unsupported protocol version")
        sys.exit(1)
    if reason_code == "Client identifier not valid":
        logging.error("Client identifier not valid")
        sys.exit(1)
    if reason_code == 0:
        logging.info("Connected successfully to MQTT broker")
    else:
        logging.error("Connection failed")
        sys.exit(1)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    logging.info("Subscribing to MQTT topics:")

    client.subscribe(TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE)
    logging.info("Subscribed to MQTT topic: %s", TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE)

    client.subscribe(TESLAMATE_MQTT_TOPIC_UPDATE_VERSION)
    logging.info("Subscribed to MQTT topic: %s", TESLAMATE_MQTT_TOPIC_UPDATE_VERSION)

    logging.info("Subscribed to all MQTT topics.")

    logging.info("Waiting for MQTT messages...")


def on_message(client, userdata, msg):  # pylint: disable=unused-argument
    """ The callback for when a PUBLISH message is received from the server."""
    global state  # pylint: disable=global-variable-not-assigned, # noqa: F824
    logging.debug("Received message: %s %s", msg.topic, msg.payload.decode())

    if msg.topic == TESLAMATE_MQTT_TOPIC_UPDATE_VERSION:
        state.update_version = msg.payload.decode()
        logging.info("Update to version %s available.", state.update_version)

    if msg.topic == TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE:
        state.update_available = msg.payload.decode() == "true"
        if msg.payload.decode() == "true":
            logging.info("A new SW update to version: %s for your Tesla is available!", state.update_version)
        if msg.payload.decode() == "false":
            logging.debug("No SW update available.")
            state.update_available_message_sent = False  # Reset the message sent flag


def setup_mqtt_client():
    """ Setup the MQTT client """
    logging.info("Setting up the MQTT client...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    username = get_env_variable(MQTT_BROKER_USERNAME, MQTT_BROKER_USERNAME_DEFAULT)
    password = get_env_variable(MQTT_BROKER_PASSWORD, MQTT_BROKER_PASSWORD_DEFAULT)
    client.username_pw_set(username, password)

    host = get_env_variable(MQTT_BROKER_HOST, MQTT_BROKER_HOST_DEFAULT)
    try:
        port = int(get_env_variable(MQTT_BROKER_PORT, MQTT_BROKER_PORT_DEFAULT))
    except ValueError as value_error_mqtt_broker_port:
        error_message_mqtt_broker_port = (f"Error: Please set the environment variable {MQTT_BROKER_PORT} "
                                          f"to a valid number and try again."
                                          )
        raise EnvironmentError(error_message_mqtt_broker_port) from value_error_mqtt_broker_port
    logging.info("Connect to MQTT broker at %s:%s", host, port)
    client.connect(host, port, MQTT_BROKER_KEEPALIVE)

    return client


def setup_telegram_bot():
    """ Setup the Telegram bot """
    logging.info("Setting up the Telegram bot...")
    bot = Bot(get_env_variable(TELEGRAM_BOT_API_KEY))
    try:
        chat_id = int(get_env_variable(TELEGRAM_BOT_CHAT_ID))
    except ValueError as value_error_chat_id:
        error_message_chat_id = (f"Error: Please set the environment variable {TELEGRAM_BOT_CHAT_ID} "
                                 f"to a valid number and try again."
                                 )
        raise EnvironmentError(error_message_chat_id) from value_error_chat_id

    logging.info("Connected to Telegram bot successfully.")
    return bot, chat_id


async def check_state_and_send_messages(bot, chat_id):
    """ Check the state and send messages if necessary """
    logging.debug("Checking state and sending messages...")
    global state  # pylint: disable=global-variable-not-assigned, # noqa: F824

    if state.update_available and not state.update_available_message_sent:
        logging.debug("Update available and message not sent.")
        if state.update_version not in ("unknown", ""):
            logging.info("A new SW update to version: %s for your Tesla is available!", state.update_version)
            message_text = "<b>" \
                "SW Update 🎁" \
                "</b>\n" \
                "A new SW update to version: " \
                + state.update_version \
                + " for your Tesla is available!"
            await send_telegram_message_to_chat_id(bot, chat_id, message_text)

            # Mark the message as sent
            state.update_available_message_sent = True
            logging.debug("Message sent flag set.")


async def send_telegram_message_to_chat_id(bot, chat_id, message_text_to_send):
    """ Send a message to a chat ID """
    logging.debug("Sending message.")
    await bot.send_message(
            chat_id,
            text=message_text_to_send,
            parse_mode=ParseMode.HTML,
        )
    logging.debug("Message sent.")


# Main function
async def main():
    """ Main function"""
    logging.info("Starting the Teslamate Telegram Bot.")
    try:
        client = setup_mqtt_client()
        bot, chat_id = setup_telegram_bot()
        start_message = "<b>" \
            "Teslamate Telegram Bot started ✅" \
            "</b>\n" \
            "and will notify as soon as a new SW version is available."
        await send_telegram_message_to_chat_id(bot, chat_id, start_message)

        client.loop_start()
        try:
            while True:
                await check_state_and_send_messages(bot, chat_id)

                logging.debug("Sleeping for 30 second.")
                await asyncio.sleep(30)
        except KeyboardInterrupt:
            logging.info("Exiting after receiving SIGINT (Ctrl+C) signal.")
    except EnvironmentError as e:
        logging.error(e)
        logging.info("Sleeping for 2 minutes before exiting or restarting, depending on your restart policy.")
        await asyncio.sleep(120)

    # clean exit
    logging.info("Disconnecting from MQTT broker.")
    client.disconnect()
    logging.info("Disconnected from MQTT broker.")
    client.loop_stop()
    logging.info("Exiting the Teslamate Telegram bot.")
    stop_message = "<b>" \
        "Teslamate Telegram Bot stopped. 🛑" \
        "</b>\n "
    await send_telegram_message_to_chat_id(bot, chat_id, stop_message)
    await bot.close()


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
