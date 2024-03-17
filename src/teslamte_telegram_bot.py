""" A simple Telegram bot that listens to MQTT messages from Teslamate and sends them to a Telegram chat."""
import os
import time
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.constants import ParseMode

########################################################################################

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
teslamate_topic_update_version =f"teslamate/cars/{CAR_ID}/update_version"

########################################################################################

# Helper functions
def get_env_variable(var_name, default_value=None):
    """ Get the environment variable or return a default value"""
    var_value = os.getenv(var_name, default_value)
    if var_value is None and var_name in [TELEGRAM_BOT_API_KEY, TELEGRAM_BOT_CHAT_ID]:
        print(f"Error: Please set the environment variable {var_name} and try again.")
        # raise EnvironmentError(f"Environment variable {var_name} is not set.")
        exit(1)
    return var_value

def on_connect(client, userdata, flags, reasonCode, properties=None):
    """ The callback for when the client receives a CONNACK response from the server."""
    print("Connected with result code "+str(reasonCode))
    if reasonCode == "Unsupported protocol version":
        print("Unsupported protocol version")
        exit(1)
    if reasonCode == "Client identifier not valid":
        print("Client identifier not valid")
        exit(1)
    if reasonCode == 0:
        print("Connected successfully to broker")
    else:
        print("Connection failed")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(teslamate_topic_update_available)
    client.subscribe(teslamate_topic_update_version)

update_version = 'unknown'
def on_message(client, userdata, msg, bot, chat_id):
    """ The callback for when a PUBLISH message is received from the server."""
    global update_version
    print(msg.topic+" "+str(msg.payload))

    if msg.topic == teslamate_topic_update_version:
        update_version = msg.payload.decode()
        print(f"Update to version {update_version} available.")

    if msg.topic == teslamate_topic_update_available:
        if msg.payload.decode() == "true":
            print(f"A new SW update to version: {update_version} for your Tesla is available!")
            bot.send_message(
                chat_id,
                text="<b>"+"SW Update"+"</b>\n"+"A new SW update to version: "+ update_version + " for your Tesla is available!",
                parse_mode=ParseMode.HTML,
            )

def setup_mqtt_client_and_telegram_bot():
    """ Setup the MQTT client """


    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    bot = Bot(get_env_variable(TELEGRAM_BOT_API_KEY))
    chat_id = get_env_variable(TELEGRAM_BOT_CHAT_ID)
    client.on_message = lambda client, userdata, msg: on_message(client, userdata, msg, bot, chat_id)

    username = get_env_variable(MQTT_BROKER_USERNAME, MQTT_BROKER_USERNAME_DEFAULT)
    password = get_env_variable(MQTT_BROKER_PASSWORD, MQTT_BROKER_PASSWORD_DEFAULT)
    client.username_pw_set(username, password)

    host = get_env_variable(MQTT_BROKER_HOST, MQTT_BROKER_HOST_DEFAULT)
    port = int(get_env_variable(MQTT_BROKER_PORT, MQTT_BROKER_PORT_DEFAULT))
    client.connect(host, port, MQTT_BROKER_KEEPALIVE)

    return client

# Main function
def main():
    """ Main function"""
    client = setup_mqtt_client_and_telegram_bot()

    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting")
    client.disconnect()
    client.loop_stop()

# Entry point
if __name__ == "__main__":
    main()
