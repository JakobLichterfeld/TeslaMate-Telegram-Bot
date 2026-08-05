"""Tests for the startup and shutdown sequence.

The failure paths are regression tests: the shutdown below the try block used
to run unconditionally and crashed with an UnboundLocalError whenever the
setup had raised.
"""

import asyncio
import types

import pytest
from telegram.error import NetworkError


class FakeClient:
    """Records what the shutdown does to the MQTT client."""

    def __init__(self, calls):
        self.calls = calls

    def loop_start(self):
        self.calls.append("loop_start")

    def disconnect(self):
        self.calls.append("disconnect")

    def loop_stop(self):
        self.calls.append("loop_stop")


class FakeBot:
    """Records what the shutdown does to the Telegram bot."""

    def __init__(self, calls):
        self.calls = calls

    async def shutdown(self):
        self.calls.append("bot.shutdown")


@pytest.fixture(name="calls")
def fixture_calls():
    return []


@pytest.fixture(name="running_bot")
def fixture_running_bot(module, monkeypatch, calls):
    """A setup that succeeds, with the main loop stopped by Ctrl+C."""
    monkeypatch.setattr(module, "setup_mqtt_client", lambda _state: FakeClient(calls))
    monkeypatch.setattr(module, "setup_telegram_bot", lambda: (FakeBot(calls), 42))

    async def interrupt(_bot, _chat_id, _state):
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "check_state_and_send_messages", interrupt)


@pytest.mark.usefixtures("instant_sleep")
def test_polls_the_state_in_a_loop(module, monkeypatch, sent_messages, calls):
    monkeypatch.setattr(module, "setup_mqtt_client", lambda _state: FakeClient(calls))
    monkeypatch.setattr(module, "setup_telegram_bot", lambda: (FakeBot(calls), 42))
    checks = []

    async def check(_bot, _chat_id, _state):
        checks.append(1)
        if len(checks) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(module, "check_state_and_send_messages", check)

    asyncio.run(module.main())

    assert len(checks) == 2
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2


@pytest.mark.usefixtures("instant_sleep", "running_bot")
def test_shuts_down_in_order(module, sent_messages, calls):
    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2
    assert "started" in sent_messages[0][1]
    assert "stopped" in sent_messages[1][1]


@pytest.mark.usefixtures("instant_sleep")
def test_stops_when_the_broker_rejects_the_connection(
    module, monkeypatch, sent_messages, calls
):
    """The connect callback cannot end the bot from paho's thread."""

    def setup(state):
        # paho reports the rejection through the state, as on_connect does.
        state.record_connection_failure("Not authorized")
        return FakeClient(calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)
    monkeypatch.setattr(module, "setup_telegram_bot", lambda: (FakeBot(calls), 42))

    async def never_called(_bot, _chat_id, _state):
        raise AssertionError("the loop must not get this far")

    monkeypatch.setattr(module, "check_state_and_send_messages", never_called)

    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2  # started, stopped


@pytest.mark.usefixtures("instant_sleep", "running_bot", "sent_messages")
def test_hands_its_own_state_to_the_client(module, monkeypatch, calls):
    seen = []

    def setup(state):
        seen.append(state)
        return FakeClient(calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)

    asyncio.run(module.main())

    assert len(seen) == 1
    assert isinstance(seen[0], module.State)


@pytest.mark.usefixtures("instant_sleep")
def test_survives_an_unreachable_broker(module, monkeypatch, sent_messages, calls):
    def refuse(_state):
        raise ConnectionRefusedError(61, "Connection refused")

    monkeypatch.setattr(module, "setup_mqtt_client", refuse)

    asyncio.run(module.main())

    assert calls == []
    assert sent_messages == []


@pytest.mark.usefixtures("instant_sleep")
def test_disconnects_the_client_when_the_telegram_setup_fails(
    module, monkeypatch, sent_messages, calls
):
    monkeypatch.setattr(module, "setup_mqtt_client", lambda _state: FakeClient(calls))

    def missing_token():
        raise OSError("Error: Please set the environment variable TELEGRAM_BOT_API_KEY")

    monkeypatch.setattr(module, "setup_telegram_bot", missing_token)

    asyncio.run(module.main())

    assert calls == ["disconnect", "loop_stop"]
    assert sent_messages == []


@pytest.mark.usefixtures("instant_sleep", "running_bot")
def test_a_failing_goodbye_does_not_hide_the_original_error(module, monkeypatch, calls):
    """Telegram being down is what ends the bot, so the goodbye fails too."""

    async def unreachable(_bot, _chat_id, text):
        # Distinct messages: the assertion below pins down which of the two
        # failures leaves main(), the original one or the one from the cleanup.
        raise NetworkError("greeting failed" if "started" in text else "goodbye failed")

    monkeypatch.setattr(module, "send_telegram_message_to_chat_id", unreachable)

    with pytest.raises(NetworkError, match="greeting failed"):
        asyncio.run(module.main())

    # Everything was still shut down before the exception left main().
    assert calls == ["disconnect", "loop_stop", "bot.shutdown"]


@pytest.mark.usefixtures("instant_sleep", "running_bot")
def test_releases_the_bot_even_when_the_goodbye_fails(module, monkeypatch, calls):
    """A failing goodbye must not cost the bot's resources."""
    sent = []

    async def fail_on_goodbye(_bot, _chat_id, text):
        sent.append(text)
        if "stopped" in text:
            raise NetworkError("Telegram is unreachable")

    monkeypatch.setattr(module, "send_telegram_message_to_chat_id", fail_on_goodbye)

    asyncio.run(module.main())

    assert len(sent) == 2
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]


@pytest.mark.usefixtures("instant_sleep", "sent_messages")
def test_a_failing_release_does_not_take_down_the_shutdown(module, monkeypatch, calls):
    """Even releasing the resources can fail; it must not raise from here."""

    class BrokenBot(FakeBot):
        async def shutdown(self):
            raise NetworkError("Telegram is unreachable")

    monkeypatch.setattr(module, "setup_mqtt_client", lambda _state: FakeClient(calls))
    monkeypatch.setattr(module, "setup_telegram_bot", lambda: (BrokenBot(calls), 42))

    async def interrupt(_bot, _chat_id, _state):
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "check_state_and_send_messages", interrupt)

    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop"]


def test_the_entry_point_runs_the_bot(module, monkeypatch):
    started = []

    def run(coroutine):
        started.append(coroutine.cr_code.co_name)
        coroutine.close()

    monkeypatch.setattr(module, "asyncio", types.SimpleNamespace(run=run))

    module.main_sync()

    assert started == ["main"]
