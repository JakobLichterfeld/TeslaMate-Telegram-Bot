"""Shared fixtures for the test suite."""

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


@pytest.fixture(name="config")
def fixture_config():
    """A complete configuration, built directly instead of from the environment."""
    return bot.Config(
        car_id=1,
        namespace="",
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_username="user",
        mqtt_password="secret",
        telegram_token="token",
        telegram_chat_id=42,
    )


@pytest.fixture(name="context")
def fixture_context(config, state):
    """What paho hands to the callbacks as user data."""
    return bot.MqttCallbackContext(config=config, state=state)


@pytest.fixture(name="configured_env")
def fixture_configured_env(monkeypatch):
    """The environment a working deployment provides."""
    monkeypatch.setenv("TELEGRAM_BOT_API_KEY", "token")
    monkeypatch.setenv("TELEGRAM_BOT_CHAT_ID", "42")


@pytest.fixture(name="message")
def fixture_message():
    """Build an MQTT message as paho hands it to the callbacks.

    The payload is real bytes, so decoding behaves like it does in
    production - including failing on bytes that are not valid UTF-8.
    """

    def build(topic, payload):
        return types.SimpleNamespace(
            topic=topic,
            payload=payload if isinstance(payload, bytes) else payload.encode(),
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


@pytest.fixture(name="instant_backoff")
def fixture_instant_backoff(monkeypatch):
    """Make the backoff after a failed start take no real time.

    Only the duration is shortened: the waiting itself stays the real
    asyncio.wait_for on the stop event, so the signal handling is exercised
    exactly as it runs in production.
    """
    monkeypatch.setattr(bot, "ERROR_BACKOFF_SECONDS", 0)
