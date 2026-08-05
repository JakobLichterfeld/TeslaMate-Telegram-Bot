"""Tests for the MQTT message callback.

The state arrives as paho's user data, so every test can hand in its own.
"""

import logging

import pytest

GRACE = 30


def version_message(module, message, version):
    return message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, version)


def availability_message(module, message, available):
    return message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, available)


def test_stores_the_announced_version(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))

    assert state.current_version() == "2026.4.1"


def test_an_available_update_becomes_due(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    due = state.pending_notification(GRACE)
    assert due.version == "2026.4.1"
    assert due.episode == 1


def test_an_update_that_is_gone_stops_being_due(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    module.on_message(None, state, availability_message(module, message, "false"))

    assert state.pending_notification(GRACE) is None


def test_availability_returning_opens_a_new_episode(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))
    state.mark_notified(1)

    module.on_message(None, state, availability_message(module, message, "false"))
    module.on_message(None, state, version_message(module, message, "2026.4.2"))
    module.on_message(None, state, availability_message(module, message, "true"))

    due = state.pending_notification(GRACE)
    assert due.episode == 2
    assert due.version == "2026.4.2"


def test_the_version_of_a_finished_episode_is_not_reused(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    module.on_message(None, state, availability_message(module, message, "false"))

    assert state.current_version() is None


def test_a_repeated_availability_message_changes_nothing(module, state, message):
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))
    state.mark_notified(1)

    module.on_message(None, state, availability_message(module, message, "true"))

    assert state.pending_notification(GRACE) is None


def test_a_damaged_availability_payload_is_ignored(module, state, message, caplog):
    """Reading anything but true/false as false would end the episode."""
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    with caplog.at_level(logging.WARNING):
        module.on_message(
            None, state, availability_message(module, message, "unavailable")
        )

    assert state.pending_notification(GRACE).version == "2026.4.1"
    assert state.current_version() == "2026.4.1"
    assert "unexpected payload" in caplog.text


@pytest.mark.parametrize("payload", ["True", "TRUE", "1", "", "yes", "unavailable"])
def test_only_the_exact_payloads_are_accepted(module, state, message, payload):
    """Tested during a running episode: an empty state cannot tell ignoring
    apart from reading the value as false, both would look the same."""
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    module.on_message(None, state, availability_message(module, message, payload))

    due = state.pending_notification(GRACE)
    assert due.episode == 1
    assert due.version == "2026.4.1"


@pytest.mark.parametrize(
    "topic_of",
    [
        lambda module: module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE,
        lambda module: module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION,
    ],
)
def test_an_undecodable_payload_is_ignored(module, state, message, caplog, topic_of):
    """Raising here would end paho's network loop, not just this message."""
    module.on_message(None, state, version_message(module, message, "2026.4.1"))
    module.on_message(None, state, availability_message(module, message, "true"))

    with caplog.at_level(logging.WARNING):
        module.on_message(None, state, message(topic_of(module), b"\xff\xfe\x00"))

    due = state.pending_notification(GRACE)
    assert due.episode == 1
    assert due.version == "2026.4.1"
    assert "undecodable payload of 3 bytes" in caplog.text


def test_ignores_unrelated_topics(module, state, message):
    module.on_message(None, state, message("teslamate/cars/1/battery_level", "42"))

    assert state.current_version() is None
    assert state.pending_notification(GRACE) is None


def test_states_do_not_leak_into_each_other(module, message):
    first, second = module.State(), module.State()

    module.on_message(first, first, version_message(module, message, "2026.4.1"))

    assert first.current_version() == "2026.4.1"
    assert second.current_version() is None
