"""Tests for the startup and shutdown sequence.

The failure paths are regression tests: the shutdown below the try block used
to run unconditionally and crashed with an UnboundLocalError whenever the
setup had raised.
"""

import asyncio
import types

import pytest


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

    async def close(self):
        self.calls.append("bot.close")


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
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.close"]
    assert len(sent_messages) == 2


@pytest.mark.usefixtures("instant_sleep", "running_bot")
def test_shuts_down_in_order(module, sent_messages, calls):
    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.close"]
    assert len(sent_messages) == 2
    assert "started" in sent_messages[0][1]
    assert "stopped" in sent_messages[1][1]


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


def test_the_entry_point_runs_the_bot(module, monkeypatch):
    started = []

    def run(coroutine):
        started.append(coroutine.cr_code.co_name)
        coroutine.close()

    monkeypatch.setattr(module, "asyncio", types.SimpleNamespace(run=run))

    module.main_sync()

    assert started == ["main"]
