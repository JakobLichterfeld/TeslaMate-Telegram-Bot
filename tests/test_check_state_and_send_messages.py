"""Tests for the notification logic."""

import asyncio


def check(module, state, chat_id=42):
    asyncio.run(module.check_state_and_send_messages(object(), chat_id, state))


def test_notifies_once_an_update_is_available(module, state, sent_messages):
    state.update_available = True
    state.update_version = "2026.4.1"

    check(module, state)

    assert len(sent_messages) == 1
    chat_id, text = sent_messages[0]
    assert chat_id == 42
    assert "2026.4.1" in text
    assert state.update_available_message_sent is True


def test_does_not_notify_twice_for_the_same_update(module, state, sent_messages):
    state.update_available = True
    state.update_version = "2026.4.1"

    check(module, state)
    check(module, state)

    assert len(sent_messages) == 1


def test_stays_quiet_without_an_update(module, state, sent_messages):
    check(module, state)

    assert sent_messages == []


def test_waits_for_the_version_before_notifying(module, state, sent_messages):
    state.update_available = True
    state.update_version = "unknown"

    check(module, state)

    assert sent_messages == []
    assert state.update_available_message_sent is False


def test_notifies_again_after_the_update_was_installed(module, state, sent_messages):
    state.update_available = True
    state.update_version = "2026.4.1"
    check(module, state)

    # TeslaMate reports the update as gone, then announces the next one.
    state.update_available = False
    state.update_available_message_sent = False
    state.update_available = True
    state.update_version = "2026.4.2"
    check(module, state)

    assert len(sent_messages) == 2
    assert "2026.4.2" in sent_messages[1][1]
