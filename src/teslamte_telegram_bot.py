""" A simple Telegram bot that listens to MQTT messages from Teslamate and sends them to a Telegram chat."""
import os
import time
import paho.mqtt.client as mqtt
from telegram.bot import Bot
from telegram.parsemode import ParseMode

########################################################################################

# Default values
car_id = 1
mqtt_broker_host_default = '127.0.0.1'
mqtt_broker_port_default = 1883
mqtt_broker_keepalive = 60
mqtt_broker_username_default = ''
mqtt_broker_password_default = ''

# Environment variables
TELEGRAM_BOT_API_KEY = 'TELEGRAM_BOT_API_KEY'
TELEGRAM_BOT_CHAT_ID = 'TELEGRAM_BOT_CHAT_ID'
MQTT_BROKER_USERNAME = 'MQTT_BROKER_USERNAME'
MQTT_BROKER_PASSWORD = 'MQTT_BROKER_PASSWORD'
MQTT_BROKER_HOST = 'MQTT_BROKER_HOST'
MQTT_BROKER_PORT = 'MQTT_BROKER_PORT'

# MQTT topics
teslamate_topic_update_available = f"teslamate/cars/{car_id}/update_available"

########################################################################################

# Global variables
bot = None
chat_id = None

# Helper functions
def get_env_variable(var_name, default_value=None):
    """ Get the environment variable or return a default value"""
    var_value = os.getenv(var_name, default_value)
    if var_value is None and var_name in [TELEGRAM_BOT_API_KEY, TELEGRAM_BOT_CHAT_ID]:
        print(f"Error: Please set the environment variable {var_name} and try again.")
        # raise EnvironmentError(f"Environment variable {var_name} is not set.")
        exit(1)
    return var_value

def on_connect(client, userdata, flags, reason_code):
    """ The callback for when the client receives a CONNACK response from the server."""
    print("Connected with result code "+str(reason_code))
    if reason_code == "Unsupported protocol version":
        print("Unsupported protocol version")
        exit(1)
    if reason_code == "Client identifier not valid":
        print("Client identifier not valid")
        exit(1)
    if reason_code == 0:
        print("Connected successfully to broker")
    else:
        print("Connection failed")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(teslamate_topic_update_available)

def on_message(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the server."""
    print(msg.topic+" "+str(msg.payload))

    if msg.payload.decode() == "true":
        print("A new SW update for your Tesla is available!")
        bot.send_message(
            chat_id,
            # text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!\n\n<b>"+msg.topic+"</b>\n"+str(msg.payload.decode()),
            text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!",
            parse_mode=ParseMode.HTML,
        )

def setup_mqtt_client():
    """ Setup the MQTT client """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    username = get_env_variable(MQTT_BROKER_USERNAME, mqtt_broker_username_default)
    password = get_env_variable(MQTT_BROKER_PASSWORD, mqtt_broker_password_default)
    client.username_pw_set(username, password)

    host = get_env_variable(MQTT_BROKER_HOST, mqtt_broker_host_default)
    port = int(get_env_variable(MQTT_BROKER_PORT, mqtt_broker_port_default))
    client.connect(host, port, mqtt_broker_keepalive)

    return client

# Main function
def main():
    """ Main function"""
    global bot
    global chat_id
    bot = Bot(get_env_variable(TELEGRAM_BOT_API_KEY))
    chat_id = get_env_variable(TELEGRAM_BOT_CHAT_ID)

    client = setup_mqtt_client()

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
