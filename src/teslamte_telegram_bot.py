""" A simple Telegram bot that listens to MQTT messages from Teslamate
and sends them to a Telegram chat."""
import os
import sys
import time
import logging
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.constants import ParseMode

##############################################################################

# Default values
CAR_ID = 1
MQTT_BROKER_HOST_DEFAULT = '127.0.0.1'
MQTT_BROKER_PORT_DEFAULT = 1883
MQTT_BROKER_KEEPALIVE = 60
MQTT_BROKER_USERNAME_DEFAULT = ''
MQTT_BROKER_PASSWORD_DEFAULT = ''

# Environment variables
TELEGRAM_BOT_API_KEY = 'TELEGRAM_BOT_API_KEY'
TELEGRAM_BOT_CHAT_ID = 'TELEGRAM_BOT_CHAT_ID'
MQTT_BROKER_USERNAME = 'MQTT_BROKER_USERNAME'
MQTT_BROKER_PASSWORD = 'MQTT_BROKER_PASSWORD'
MQTT_BROKER_HOST = 'MQTT_BROKER_HOST'
MQTT_BROKER_PORT = 'MQTT_BROKER_PORT'

# MQTT topics
teslamate_topic_update_available = f"teslamate/cars/{CAR_ID}/update_available"
teslamate_topic_update_version = f"teslamate/cars/{CAR_ID}/update_version"

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


# Helper functions
def get_env_variable(var_name, default_value=None):
    """ Get the environment variable or return a default value"""
    logging.debug("Getting environment variable %s", var_name)
    var_value = os.getenv(var_name, default_value)
    logging.debug("Environment variable %s: %s", var_name, var_value)
    if var_value is None and var_name in [TELEGRAM_BOT_API_KEY, TELEGRAM_BOT_CHAT_ID]:
        logging.error("Error: Please set the environment variable %s and try again.", var_name)
        # raise EnvironmentError(f"Environment variable {var_name} is not set.")
        sys.exit(1)
    return var_value


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
    client.subscribe(teslamate_topic_update_available)
    logging.info("Subscribed to MQTT topic: %s", teslamate_topic_update_available)

    client.subscribe(teslamate_topic_update_version)
    logging.info("Subscribed to MQTT topic: %s", teslamate_topic_update_version)

    logging.info("Subscribed to all MQTT topics.")

    logging.info("Waiting for MQTT messages...")


def on_message(client, userdata, msg):  # pylint: disable=unused-argument
    """ The callback for when a PUBLISH message is received from the server."""
    global state  # pylint: disable=global-variable-not-assigned
    logging.debug("Received message: %s %s", msg.topic, msg.payload.decode())

    if msg.topic == teslamate_topic_update_version:
        state.update_version = msg.payload.decode()
        logging.info("Update to version %s available.", state.update_version)

    if msg.topic == teslamate_topic_update_available:
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
    port = int(get_env_variable(MQTT_BROKER_PORT, MQTT_BROKER_PORT_DEFAULT))
    logging.info("Connect to MQTT broker at %s:%s", host, port)
    client.connect(host, port, MQTT_BROKER_KEEPALIVE)

    return client


def setup_telegram_bot():
    """ Setup the Telegram bot """
    logging.info("Setting up the Telegram bot...")
    bot = Bot(get_env_variable(TELEGRAM_BOT_API_KEY))
    chat_id = get_env_variable(TELEGRAM_BOT_CHAT_ID)

    logging.info("Connected to Telegram bot successfully.")
    return bot, chat_id


def check_state_and_send_messages(bot, chat_id):
    """ Check the state and send messages if necessary """
    logging.debug("Checking state and sending messages...")
    global state  # pylint: disable=global-variable-not-assigned

    if state.update_available and not state.update_available_message_sent:
        logging.debug("Update available and message not sent.")
        if state.update_version != "unknown":
            logging.info("A new SW update to version: %s for your Tesla is available!", state.update_version)
            message_text = "<b>" \
                "SW Update" \
                "</b>\n" \
                "A new SW update to version: " \
                + state.update_version \
                + " for your Tesla is available!"

        logging.debug("Sending message.")
        bot.send_message(
            chat_id,
            text=message_text,
            parse_mode=ParseMode.HTML,
        )
        logging.debug("Message sent.")

        # Mark the message as sent
        state.update_available_message_sent = True
        logging.debug("Message sent flag set.")


# Main function
def main():
    """ Main function"""
    logging.info("Starting the Teslamate Telegram bot.")
    client = setup_mqtt_client()
    bot, chat_id = setup_telegram_bot()

    client.loop_start()
    try:
        while True:
            check_state_and_send_messages(bot, chat_id)

            logging.debug("Sleeping for 1 second.")
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting after receiving SIGINT (Ctrl+C) signal.")

    logging.info("Disconnecting from MQTT broker.")
    client.disconnect()
    logging.info("Disconnected from MQTT broker.")
    client.loop_stop()
    logging.info("Exiting the Teslamate Telegram bot.")


# Entry point
if __name__ == "__main__":
    main()
