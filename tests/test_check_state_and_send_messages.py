"""Tests for the notification logic.

One message per availability episode. The version is optional: if it has not
arrived when the grace period is over, the message goes out without it.
"""

import asyncio

import pytest


@pytest.fixture(name="clock")
def fixture_clock():
    """A hand-cranked clock, so the grace period costs no real time."""

    class Clock:
        def __init__(self):
            self.now = 1000.0

        def __call__(self):
            return self.now

        def advance(self, seconds):
            self.now += seconds

    return Clock()


@pytest.fixture(name="state")
def fixture_state(module, clock):
    return module.State(clock=clock)


def check(module, state, chat_id=42):
    asyncio.run(module.check_state_and_send_messages(object(), chat_id, state))


def test_notifies_with_the_version_when_it_is_known(module, state, sent_messages):
    state.record_version("2026.4.1")
    state.record_availability(True)

    check(module, state)

    assert len(sent_messages) == 1
    chat_id, text = sent_messages[0]
    assert chat_id == 42
    assert "2026.4.1" in text


def test_holds_back_while_waiting_for_the_version(module, state, sent_messages):
    state.record_availability(True)

    check(module, state)

    assert sent_messages == []


def test_notifies_without_a_version_once_the_wait_is_over(
    module, state, clock, sent_messages
):
    state.record_availability(True)

    clock.advance(module.VERSION_GRACE_PERIOD_SECONDS)
    check(module, state)

    assert len(sent_messages) == 1
    _, text = sent_messages[0]
    assert "A new SW update for your Tesla is available!" in text
    assert "version" not in text


def test_a_version_arriving_later_does_not_notify_twice(
    module, state, clock, sent_messages
):
    state.record_availability(True)
    clock.advance(module.VERSION_GRACE_PERIOD_SECONDS)
    check(module, state)

    state.record_version("2026.4.1")
    check(module, state)

    assert len(sent_messages) == 1


def test_does_not_notify_twice_within_one_episode(module, state, sent_messages):
    state.record_version("2026.4.1")
    state.record_availability(True)

    check(module, state)
    state.record_availability(True)  # retained message, reconnect
    check(module, state)

    assert len(sent_messages) == 1


def test_notifies_again_for_a_new_episode(module, state, sent_messages):
    state.record_version("2026.4.1")
    state.record_availability(True)
    check(module, state)

    state.record_availability(False)
    state.record_version("2026.4.2")
    state.record_availability(True)
    check(module, state)

    assert len(sent_messages) == 2
    assert "2026.4.2" in sent_messages[1][1]


def test_stays_quiet_without_an_update(module, state, sent_messages):
    check(module, state)

    assert sent_messages == []


def test_an_episode_starting_during_the_send_is_not_swallowed(
    module, state, monkeypatch
):
    """The state can move on while the notification is in flight.

    Acknowledging the current state instead of the episode that was sent
    would mark the newer episode as reported, and it would never go out.
    """
    sent = []

    async def send_and_move_on(_bot, _chat_id, text):
        sent.append(text)
        if "2026.4.1" in text:
            # While Telegram is being talked to: the update is installed and
            # the next one is announced.
            state.record_availability(False)
            state.record_version("2026.4.2")
            state.record_availability(True)

    monkeypatch.setattr(module, "send_telegram_message_to_chat_id", send_and_move_on)

    state.record_version("2026.4.1")
    state.record_availability(True)
    check(module, state)

    assert state.pending_notification(module.VERSION_GRACE_PERIOD_SECONDS).episode == 2

    check(module, state)

    assert len(sent) == 2
    assert "2026.4.2" in sent[1]
