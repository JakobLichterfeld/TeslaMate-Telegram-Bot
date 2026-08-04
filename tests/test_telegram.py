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


@pytest.fixture(name="telegram_env")
def fixture_telegram_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_API_KEY", "token")
    monkeypatch.setenv("TELEGRAM_BOT_CHAT_ID", "4711")


@pytest.mark.usefixtures("fake_bot_class", "telegram_env")
def test_builds_the_bot_from_the_environment(module):
    bot, chat_id = module.setup_telegram_bot()

    assert bot.token == "token"
    assert chat_id == 4711


@pytest.mark.usefixtures("fake_bot_class")
def test_rejects_a_chat_id_that_is_not_a_number(module, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_API_KEY", "token")
    monkeypatch.setenv("TELEGRAM_BOT_CHAT_ID", "not-a-chat")

    with pytest.raises(OSError, match="TELEGRAM_BOT_CHAT_ID"):
        module.setup_telegram_bot()


@pytest.mark.usefixtures("fake_bot_class")
def test_requires_the_api_key(module, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_API_KEY", raising=False)

    with pytest.raises(OSError, match="TELEGRAM_BOT_API_KEY"):
        module.setup_telegram_bot()


def test_sends_the_message_as_html(module):
    bot = RecordingBot()

    asyncio.run(module.send_telegram_message_to_chat_id(bot, 4711, "<b>hi</b>"))

    assert bot.sent == [(4711, "<b>hi</b>", module.ParseMode.HTML)]
