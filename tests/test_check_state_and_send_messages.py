"""Tests for the notification logic."""

import asyncio


def check(module, state, chat_id=42):
    asyncio.run(module.check_state_and_send_messages(object(), chat_id, state))


def announce(state, version):
    state.record_version(version)
    state.record_availability(True)


def test_notifies_once_an_update_is_available(module, state, sent_messages):
    announce(state, "2026.4.1")

    check(module, state)

    assert len(sent_messages) == 1
    chat_id, text = sent_messages[0]
    assert chat_id == 42
    assert "2026.4.1" in text
    assert state.pending_update() is None


def test_does_not_notify_twice_for_the_same_update(module, state, sent_messages):
    announce(state, "2026.4.1")

    check(module, state)
    check(module, state)

    assert len(sent_messages) == 1


def test_stays_quiet_without_an_update(module, state, sent_messages):
    check(module, state)

    assert sent_messages == []


def test_waits_for_the_version_before_notifying(module, state, sent_messages):
    state.record_availability(True)

    check(module, state)

    assert sent_messages == []


def test_notifies_again_after_the_update_was_installed(module, state, sent_messages):
    announce(state, "2026.4.1")
    check(module, state)

    # TeslaMate reports the update as gone, then announces the next one.
    state.record_availability(False)
    announce(state, "2026.4.2")
    check(module, state)

    assert len(sent_messages) == 2
    assert "2026.4.2" in sent_messages[1][1]


def test_an_update_announced_during_the_send_is_not_swallowed(
    module, state, monkeypatch
):
    """The state can move on while the notification is in flight.

    Acknowledging the current state instead of the version that was sent
    would mark the newer update as reported, and it would never go out.
    """
    sent = []

    async def send_and_move_on(_bot, _chat_id, text):
        sent.append(text)
        if "2026.4.1" in text:
            # While Telegram is being talked to: the update is installed and
            # the next one is announced.
            state.record_availability(False)
            announce(state, "2026.4.2")

    monkeypatch.setattr(module, "send_telegram_message_to_chat_id", send_and_move_on)

    announce(state, "2026.4.1")
    check(module, state)

    assert state.pending_update() == "2026.4.2"

    check(module, state)

    assert len(sent) == 2
    assert "2026.4.2" in sent[1]
