"""Shared fixtures for the test suite."""

import asyncio
import types

import pytest

import teslamate_telegram_bot as bot


@pytest.fixture(name="module")
def fixture_module():
    """The module under test."""
    return bot


@pytest.fixture(name="state")
def fixture_state():
    """A fresh application state."""
    return bot.State()


@pytest.fixture(name="message")
def fixture_message():
    """Build an MQTT message as paho hands it to the callbacks."""

    def build(topic, payload):
        return types.SimpleNamespace(
            topic=topic,
            payload=types.SimpleNamespace(decode=lambda: payload),
        )

    return build


@pytest.fixture(name="sent_messages")
def fixture_sent_messages(monkeypatch):
    """Capture what would be sent to Telegram instead of sending it."""
    sent = []

    async def send(_bot, chat_id, text):
        sent.append((chat_id, text))

    monkeypatch.setattr(bot, "send_telegram_message_to_chat_id", send)
    return sent


@pytest.fixture(name="instant_sleep")
def fixture_instant_sleep(monkeypatch):
    """Skip the waits in main() without touching the real asyncio module."""

    async def sleep(_seconds):
        await asyncio.sleep(0)

    monkeypatch.setattr(bot, "asyncio", types.SimpleNamespace(sleep=sleep))
