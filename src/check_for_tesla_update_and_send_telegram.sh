#!/bin/sh
mqtt_broker=xxx.xxx.xxx.xxx

topic=teslamate/cars/1/update_available
#topic=teslamate/cars/1/version
#topic=teslamate/cars/1/state

mqtt_answer=$(mosquitto_sub -h $mqtt_broker -t $topic -C 1 --qos 2)


#Telegram
telegram_bot_token=SECRET:MORE_SECRET
telegram_chat_id=SECRET_CHAT_ID
telegram_url_send_message=https://api.telegram.org/bot$telegram_bot_token/sendMessage

#message_title="Teslamate"
message_text="$mqtt_answer"

curl -s -S -X POST $telegram_url_send_message -d chat_id=$telegram_chat_id -d text="$message_text" >/dev/null 2>&1
