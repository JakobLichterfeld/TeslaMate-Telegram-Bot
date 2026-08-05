"""Tests for wiring up the Telegram bot and sending messages."""

import asyncio

import pytest


class RecordingBot:
    """Stands in for telegram.Bot and records what was sent."""

    def __init__(self, token=None):
        self.token = token
        self.sent = []

    async def send_message(self, chat_id, text, parse_mode=None):
        self.sent.append((chat_id, text, parse_mode))


@pytest.fixture(name="fake_bot_class")
def fixture_fake_bot_class(module, monkeypatch):
    monkeypatch.setattr(module, "Bot", RecordingBot)
    return RecordingBot


@pytest.mark.usefixtures("fake_bot_class")
def test_builds_the_bot_from_the_config(module, config):
    """The token comes from the config, not from the environment again."""
    bot = module.setup_telegram_bot(config)

    assert bot.token == "token"


def test_sends_the_message_as_html(module):
    bot = RecordingBot()

    asyncio.run(module.send_telegram_message_to_chat_id(bot, 4711, "<b>hi</b>"))

    assert bot.sent == [(4711, "<b>hi</b>", module.ParseMode.HTML)]
