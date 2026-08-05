"""Tests for the startup and shutdown sequence.

The failure paths are regression tests: the shutdown below the try block used
to run unconditionally and crashed with an UnboundLocalError whenever the
setup had raised.
"""

import asyncio
import os
import signal
import time
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


def bot_setup(bot):
    """A setup_telegram_bot stand-in handing back an already prepared bot."""

    async def setup(_config):
        return bot

    return setup


class GrantedCode:
    """A SUBACK reason code that means the broker accepted the topic."""

    is_failure = False


def confirmed_client(context, calls):
    """A client whose broker confirms both subscriptions, as a healthy one does."""
    context.status.expect_subscription(1)
    context.status.record_subscription_result(1, [GrantedCode()])
    return FakeClient(calls)


@pytest.fixture(name="calls")
def fixture_calls():
    return []


def raise_to_self(signal_number):
    """Send a signal to this process, as Docker or a terminal would."""
    os.kill(os.getpid(), signal_number)


@pytest.fixture(name="running_bot")
def fixture_running_bot(module, monkeypatch, calls):
    """A setup that succeeds, with the main loop stopped by SIGTERM."""
    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def stop(_bot, _chat_id, _state):
        raise_to_self(signal.SIGTERM)

    monkeypatch.setattr(module, "check_state_and_send_messages", stop)


@pytest.mark.usefixtures("configured_env", "instant_backoff")
@pytest.mark.parametrize("signal_number", [signal.SIGINT, signal.SIGTERM])
def test_stops_on_a_signal(module, monkeypatch, sent_messages, calls, signal_number):
    """Ctrl+C sends SIGINT, `docker stop` and systemd send SIGTERM.

    The signal is really sent to this process: without a handler SIGTERM
    would end the test run outright, which is exactly what it does to the bot.
    """
    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def stop(_bot, _chat_id, _state):
        raise_to_self(signal_number)

    monkeypatch.setattr(module, "check_state_and_send_messages", stop)

    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_polls_the_state_in_a_loop(module, monkeypatch, sent_messages, calls):
    # The wait between two rounds is a real one now: it ends early on a
    # signal, so shorten it instead of sitting out the poll interval.
    monkeypatch.setattr(module, "POLL_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))
    checks = []

    async def check(_bot, _chat_id, _state):
        checks.append(1)
        if len(checks) == 2:
            raise_to_self(signal.SIGTERM)

    monkeypatch.setattr(module, "check_state_and_send_messages", check)

    asyncio.run(module.main())

    assert len(checks) == 2
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2


@pytest.mark.usefixtures("configured_env", "instant_backoff", "running_bot")
def test_shuts_down_in_order(module, sent_messages, calls):
    status = asyncio.run(module.main())

    assert status == module.EXIT_SUCCESS
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    assert len(sent_messages) == 2
    assert "started" in sent_messages[0][1]
    assert "stopped" in sent_messages[1][1]


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_stops_when_the_broker_rejects_the_connection(
    module, monkeypatch, sent_messages, calls
):
    """The connect callback cannot end the bot from paho's thread."""

    def setup(context):
        # paho reports the rejection through the state, as on_connect does.
        context.status.record_connection_failure("Not authorized")
        return FakeClient(calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def never_called(_bot, _chat_id, _state):
        raise AssertionError("the loop must not get this far")

    monkeypatch.setattr(module, "check_state_and_send_messages", never_called)

    status = asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]
    # No start message: the rejection is known before the bot claims to run.
    assert len(sent_messages) == 1
    assert "stopped" in sent_messages[0][1]
    assert status == module.EXIT_FAILURE


@pytest.mark.usefixtures(
    "configured_env", "instant_backoff", "running_bot", "sent_messages"
)
def test_hands_a_context_of_its_own_to_the_client(module, monkeypatch, calls):
    """Config and state travel to the callbacks through paho's user data."""
    seen = []

    def setup(context):
        seen.append(context)
        return confirmed_client(context, calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)

    asyncio.run(module.main())

    assert len(seen) == 1
    assert isinstance(seen[0], module.MqttCallbackContext)
    assert isinstance(seen[0].state, module.State)
    assert isinstance(seen[0].config, module.Config)


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_survives_an_unreachable_broker(module, monkeypatch, sent_messages, calls):
    def refuse(_context):
        raise ConnectionRefusedError(61, "Connection refused")

    monkeypatch.setattr(module, "setup_mqtt_client", refuse)

    status = asyncio.run(module.main())

    assert calls == []
    assert sent_messages == []
    # A supervisor set to restart on failure has to see one.
    assert status == module.EXIT_FAILURE


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_disconnects_the_client_when_the_telegram_setup_fails(
    module, monkeypatch, sent_messages, calls
):
    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )

    async def missing_token(_config):
        raise OSError("Error: Please set the environment variable TELEGRAM_BOT_API_KEY")

    monkeypatch.setattr(module, "setup_telegram_bot", missing_token)

    asyncio.run(module.main())

    assert calls == ["disconnect", "loop_stop"]
    assert sent_messages == []


@pytest.mark.usefixtures("configured_env", "instant_backoff", "running_bot")
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
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]


@pytest.mark.usefixtures("configured_env", "instant_backoff", "running_bot")
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


@pytest.mark.usefixtures("configured_env", "instant_backoff", "sent_messages")
def test_a_failing_release_does_not_take_down_the_shutdown(module, monkeypatch, calls):
    """Even releasing the resources can fail; it must not raise from here."""

    class BrokenBot(FakeBot):
        async def shutdown(self):
            raise NetworkError("Telegram is unreachable")

    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(BrokenBot(calls)))

    async def stop(_bot, _chat_id, _state):
        raise_to_self(signal.SIGTERM)

    monkeypatch.setattr(module, "check_state_and_send_messages", stop)

    asyncio.run(module.main())

    assert calls == ["loop_start", "disconnect", "loop_stop"]


@pytest.mark.usefixtures("configured_env")
def test_a_signal_during_the_backoff_ends_the_wait(module, monkeypatch, calls):
    """`docker stop` during the backoff after a failed start must be heard."""
    monkeypatch.setattr(module, "ERROR_BACKOFF_SECONDS", 5)
    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )

    async def fail_after_the_signal(_config):
        raise_to_self(signal.SIGTERM)
        raise OSError("Error: Please set the environment variable TELEGRAM_BOT_API_KEY")

    monkeypatch.setattr(module, "setup_telegram_bot", fail_after_the_signal)

    started = time.monotonic()
    status = asyncio.run(module.main())
    elapsed = time.monotonic() - started

    assert elapsed < 1  # not the five seconds of the backoff
    assert calls == ["disconnect", "loop_stop"]
    # Asked to stop while backing off: wanted, so not a failure.
    assert status == module.EXIT_SUCCESS


@pytest.mark.usefixtures("configured_env", "sent_messages")
def test_restores_signal_handlers_it_found(module, monkeypatch, calls):
    """Removing a handler resets it to the default, which would clobber one
    the surrounding process had installed."""

    def previous_handler(_number, _frame):
        pass  # pragma: no cover - never invoked, only registered

    monkeypatch.setattr(
        module, "setup_mqtt_client", lambda context: confirmed_client(context, calls)
    )
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def stop(_bot, _chat_id, _state):
        raise_to_self(signal.SIGTERM)

    monkeypatch.setattr(module, "check_state_and_send_messages", stop)
    signal.signal(signal.SIGTERM, previous_handler)
    try:
        asyncio.run(module.main())

        assert signal.getsignal(signal.SIGTERM) is previous_handler
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)


@pytest.mark.parametrize(
    "status", [0, 1]
)  # what main() reports, whatever the reason was
def test_the_entry_point_exits_with_the_status_of_the_run(module, monkeypatch, status):
    started = []

    def run(coroutine):
        started.append(coroutine.cr_code.co_name)
        coroutine.close()
        return status

    monkeypatch.setattr(module, "asyncio", types.SimpleNamespace(run=run))

    with pytest.raises(SystemExit) as exit_info:
        module.main_sync()

    assert started == ["main"]
    assert exit_info.value.code == status


class RefusedCode:
    """A SUBACK reason code that means the broker denied the topic."""

    is_failure = True

    def __str__(self):
        return "Not authorized"


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_does_not_claim_to_run_when_a_subscription_is_refused(
    module, monkeypatch, sent_messages, calls
):
    """An ACL may allow the connection and forbid the topic.

    The bot would then look healthy and never notify, so the refusal has to
    end the start instead of being announced as success.
    """

    def setup(context):
        context.status.expect_subscription(1)
        context.status.record_subscription_result(1, [RefusedCode()])
        return FakeClient(calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def never_called(_bot, _chat_id, _state):
        raise AssertionError("the loop must not get this far")

    monkeypatch.setattr(module, "check_state_and_send_messages", never_called)

    status = asyncio.run(module.main())

    assert [text for _, text in sent_messages if "started" in text] == []
    assert status == module.EXIT_FAILURE
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_gives_up_when_no_suback_arrives(module, monkeypatch, sent_messages, calls):
    """A broker that never answers must not leave the bot hanging."""
    monkeypatch.setattr(module, "MQTT_READY_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(module, "setup_mqtt_client", lambda _context: FakeClient(calls))
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    status = asyncio.run(module.main())

    assert [text for _, text in sent_messages if "started" in text] == []
    assert status == module.EXIT_FAILURE


class LateBroker:
    """A broker status that reports readiness only on the second look."""

    def __init__(self):
        self.checks = 0

    def failure(self):
        return None

    def subscriptions_ready(self):
        self.checks += 1
        return self.checks > 1


def test_waits_for_a_suback_that_takes_a_moment(module, monkeypatch):
    """The confirmation rarely arrives before the first look."""
    monkeypatch.setattr(module, "MQTT_READY_POLL_SECONDS", 0)
    state = LateBroker()

    async def wait():
        await module.wait_until_subscribed(state, asyncio.Event())

    asyncio.run(wait())

    assert state.checks == 2


def test_the_loop_stops_when_the_connection_is_lost_later(module, context):
    """A reconnect can be rejected long after the start succeeded."""
    context.status.record_connection_failure("Not authorized")

    async def run():
        await module.run_until_stopped(None, 42, context, asyncio.Event())

    with pytest.raises(OSError, match="rejected the connection"):
        asyncio.run(run())


@pytest.mark.usefixtures("configured_env", "instant_backoff")
def test_does_not_claim_to_run_when_stopped_while_waiting(
    module, monkeypatch, sent_messages, calls
):
    """A stop during the wait leaves the subscriptions unconfirmed.

    Announcing a running bot then would claim something nobody confirmed.
    """

    def setup(_context):
        raise_to_self(signal.SIGTERM)  # `docker stop` while the SUBACK is due
        return FakeClient(calls)

    monkeypatch.setattr(module, "setup_mqtt_client", setup)
    monkeypatch.setattr(module, "setup_telegram_bot", bot_setup(FakeBot(calls)))

    async def never_called(_bot, _chat_id, _state):
        raise AssertionError("the loop must not get this far")

    monkeypatch.setattr(module, "check_state_and_send_messages", never_called)

    status = asyncio.run(module.main())

    assert [text for _, text in sent_messages if "started" in text] == []
    assert status == module.EXIT_SUCCESS  # a requested stop, not a failure
    assert calls == ["loop_start", "disconnect", "loop_stop", "bot.shutdown"]


def test_the_loop_stops_when_a_later_subscription_is_refused(module, context):
    """A reconnect can be answered with an ACL denial long after the start."""
    context.status.record_subscription_failure("Not authorized")

    async def run():
        await module.run_until_stopped(None, 42, context, asyncio.Event())

    with pytest.raises(OSError, match="refused a subscription"):
        asyncio.run(run())


class Clock:
    """A hand-cranked clock, so a timeout costs no real time."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def reconnected_context(module, config, state, clock):
    """A context whose broker just reconnected and owes two SUBACKs."""
    status = module.BrokerStatus(clock=clock)
    # The grace is timed from here, not from the loop noticing.
    status.reset_subscriptions()
    status.expect_subscription(1)
    return module.MqttCallbackContext(config=config, state=state, status=status)


def test_the_loop_gives_up_when_a_reconnect_is_never_confirmed(
    module, config, state, monkeypatch
):
    """A reconnect starts the subscriptions over; a silent broker leaves the
    bot deaf without anyone refusing anything."""
    monkeypatch.setattr(module, "POLL_INTERVAL_SECONDS", 0)
    clock = Clock()
    context = reconnected_context(module, config, state, clock)

    async def check(_bot, _chat_id, _state):
        clock.advance(module.MQTT_READY_TIMEOUT_SECONDS)

    monkeypatch.setattr(module, "check_state_and_send_messages", check)

    async def run():
        await module.run_until_stopped(None, 42, context, asyncio.Event())

    with pytest.raises(OSError, match="stopped confirming"):
        asyncio.run(run())


def test_a_confirmed_reconnect_clears_the_deadline(module, config, state, monkeypatch):
    """Once the broker answers again, the grace starts over."""
    monkeypatch.setattr(module, "POLL_INTERVAL_SECONDS", 0)
    clock = Clock()
    context = reconnected_context(module, config, state, clock)
    rounds = []

    async def check(_bot, _chat_id, _state):
        rounds.append(1)
        if len(rounds) == 1:
            # Late, but within the grace: the SUBACK arrives.
            clock.advance(module.MQTT_READY_TIMEOUT_SECONDS - 1)
            context.status.record_subscription_result(1, [GrantedCode()])
        else:
            clock.advance(module.MQTT_READY_TIMEOUT_SECONDS)
            raise KeyboardInterrupt  # ends the loop without a failure

    monkeypatch.setattr(module, "check_state_and_send_messages", check)

    async def run():
        await module.run_until_stopped(None, 42, context, asyncio.Event())

    with pytest.raises(KeyboardInterrupt):
        asyncio.run(run())

    assert len(rounds) == 2  # the second round did not run into the timeout
