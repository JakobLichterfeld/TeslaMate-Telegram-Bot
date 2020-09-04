# TeslaMate Telegram Bot

A telegram bot which sends a message if an update for your Tesla is available (use TeslaMate MQTT)

[![latest release](https://img.shields.io/github/v/release/JakobLichterfeld/TeslaMate_Telegram_Bot)](https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/releases/latest)
[![donation](https://img.shields.io/badge/Donate-PayPal-informational.svg?logo=paypal)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ZE9EHN48GYWMN&source=url)

A telegram bot which sends a message if an update for your Tesla is available (know thru TeslaMate MQTT topic)

## Table of contents

- [TeslaMate Telegram Bot](#teslamate-telegram-bot)
  - [Table of contents](#table-of-contents)
  - [Features](#features)
  - [Dependencies](#dependencies)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Update](#update)
  - [Contributing](#contributing)
  - [Donation](#donation)
  - [Disclaimer](#disclaimer)

## Features

- [x] Sends a telegram message to you if an update for your tesla is available

## Dependencies

- [TeslaMate](https://github.com/adriankumpf/teslamate)
- [mosquitto](https://mosquitto.org/)
- [Telegram](https://telegram.org/)

## Requirements

- A Machine that's always on and runs [TeslaMate](https://github.com/adriankumpf/teslamate)
- External internet access, to send telegram messages.
- A mobile with [Telegram](https://telegram.org/) client installed
- your own Telegram Bot, see [Creating a new telegram bot](https://core.telegram.org/bots#6-botfather)
- your own Telegram chat id, see [get your telegram chat id](https://docs.influxdata.com/kapacitor/v1.5/event_handlers/telegram/#get-your-telegram-chat-id)

## Installation

Install [Dependencies](#dependencies) and fulfill the [Requirements](#requirements).

It is recommended to backup your data first.

This document provides the necessary steps for installation of TeslaMate Telegram Bot on a linux system.

This setup is recommended only if you are running TeslaMate Telegram Bot **on your home network**, as otherwise your telegram API tokens might be at risk.

Before the first install you need to set up a telegram bot. For doing so, see [Requirements](#requirements).

Open the files ```src/mqtt_config.py``` and ```src/telegram_config.py``` and adopt according to your own config.

You also need to install the required pip packages

```shell
python -m pip install -r ./src/requirements.txt
```

## Usage

Execute the file ```src/teslamte_telegram_bot.py``` from linux bash with ```python ./src/teslamte_telegram_bot.py``` or, depending on your system ```python3 ./src/teslamte_telegram_bot.py```

## Update

Check out the [release notes](https://github.com/JakobLichterfeld/TeslaMate_Telegram_Bot/releases) before upgrading!

## Contributing

All contributions are welcome and greatly appreciated!

## Donation

Maintaining this project isn't effortless, or free. If you would like to kick in and help me cover those costs, that would be awesome. If you don't, no problem; just share your love and show your support.

<p align="center">
  <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ZE9EHN48GYWMN&source=url">
    <img src="screenshots/paypal-donate-button.png" alt="Donate with PayPal" />
  </a>
</p>

## Disclaimer

Please note that the use of the Tesla API in general and this software in particular is not endorsed by Tesla. Use at your own risk.
