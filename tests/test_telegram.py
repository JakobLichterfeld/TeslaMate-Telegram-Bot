"""Tests for wiring up the Telegram bot and sending messages."""

import asyncio

import pytest
from telegram.error import InvalidToken


class RecordingBot:
    """Stands in for telegram.Bot and records what was sent."""

    def __init__(self, token=None):
        self.token = token
        self.sent = []
        self.lifecycle = []

    async def initialize(self):
        self.lifecycle.append("initialize")

    async def shutdown(self):
        self.lifecycle.append("shutdown")

    async def send_message(self, chat_id, text, parse_mode=None):
        self.sent.append((chat_id, text, parse_mode))


@pytest.fixture(name="fake_bot_class")
def fixture_fake_bot_class(module, monkeypatch):
    monkeypatch.setattr(module, "Bot", RecordingBot)
    return RecordingBot


@pytest.mark.usefixtures("fake_bot_class")
def test_builds_the_bot_from_the_config(module, config):
    """The token comes from the config, not from the environment again."""
    bot = asyncio.run(module.setup_telegram_bot(config))

    assert bot.token == "token"


@pytest.mark.usefixtures("fake_bot_class")
def test_opens_the_lifecycle_the_shutdown_closes(module, config):
    """Constructing a Bot is not enough to release it again.

    python-telegram-bot only closes the HTTP client for a bot that was
    initialized; without this the shutdown returns straight away and the
    connections stay open.
    """
    bot = asyncio.run(module.setup_telegram_bot(config))

    assert bot.lifecycle == ["initialize"]


def test_releases_a_bot_that_cannot_be_initialized(module, monkeypatch, config):
    """A rejected token leaves an initialized request object behind.

    The bot never reaches the caller then, so nobody else can release it.
    """
    built = []

    class RejectedBot(RecordingBot):
        async def initialize(self):
            await super().initialize()
            raise InvalidToken("rejected")

    def build(token):
        built.append(RejectedBot(token))
        return built[-1]

    monkeypatch.setattr(module, "Bot", build)

    with pytest.raises(InvalidToken):
        asyncio.run(module.setup_telegram_bot(config))

    assert built[0].lifecycle == ["initialize", "shutdown"]


def test_sends_the_message_as_html(module):
    bot = RecordingBot()

    asyncio.run(module.send_telegram_message_to_chat_id(bot, 4711, "<b>hi</b>"))

    assert bot.sent == [(4711, "<b>hi</b>", module.ParseMode.HTML)]
