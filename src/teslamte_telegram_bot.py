import os
import time

import paho.mqtt.client as mqtt

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# initializing the bot with API_KEY and CHAT_ID
if os.getenv('TELEGRAM_BOT_API_KEY') == None:
    print("Error: Please set the environment variable TELEGRAM_BOT_API_KEY and try again.")
    exit(1)
bot = Bot(os.getenv('TELEGRAM_BOT_API_KEY'))

if os.getenv('TELEGRAM_BOT_CHAT_ID') == None:
    print("Error: Please set the environment variable TELEGRAM_BOT_CHAT_ID and try again.")
    exit(1)
chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')

# based on example from https://pypi.org/project/paho-mqtt/
# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc == 0:
        print("Connected successfully to broker")
    else:
        print("Connection failed")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # client.subscribe("teslamate/cars/1/version")
    client.subscribe("teslamate/cars/1/update_available")


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))

    if msg.payload.decode() == "true":
        print("A new SW update for your Tesla is available!")
        bot.send_message(
            chat_id,
            # text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!\n\n<b>"+msg.topic+"</b>\n"+str(msg.payload.decode()),
            text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!",
            parse_mode=ParseMode.HTML,
        )


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(os.getenv('MQTT_BROKER_HOST', '127.0.0.1'),
               int(os.getenv('MQTT_BROKER_PORT', 1883)), 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()


client.loop_start()  # start the loop
try:

    while True:

        time.sleep(1)

except KeyboardInterrupt:

    print("exiting")


client.disconnect()

client.loop_stop()
