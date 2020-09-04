# import config data
import telegram_config
import mqtt_config

import paho.mqtt.client as mqtt

import time

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# initializing the bot with API
bot = Bot(telegram_config.telegram_bot_data['api_key'])

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc == 0:
        print("Connected successfully to broker")
    else:
        print("Connection failed")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    #client.subscribe("teslamate/cars/1/version")
    client.subscribe("teslamate/cars/1/update_available")


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))

    if msg.payload.decode() == "true":
        print("A new SW update for your Tesla is available!")
        bot.send_message(
            chat_id=telegram_config.telegram_bot_data['chat_id'],
            # text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!\n\n<b>"+msg.topic+"</b>\n"+str(msg.payload.decode()),
            text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!",
            parse_mode=ParseMode.HTML,
        )


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_config.mqtt_data['mqtt_broker_host'], int(
    mqtt_config.mqtt_data['mqtt_broker_port']), 60)


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
