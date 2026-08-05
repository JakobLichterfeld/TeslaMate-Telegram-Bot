"""Tests for the MQTT message callback.

Settings and state arrive together as paho's user data, so every test hands
in its own context and nothing is shared through the module.
"""

import logging

import pytest

GRACE = 30


def version_message(context, message, version):
    return message(context.config.update_version_topic, version)


def availability_message(context, message, available):
    return message(context.config.update_available_topic, available)


def test_stores_the_announced_version(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))

    assert context.state.current_version() == "2026.4.1"


def test_an_available_update_becomes_due(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    due = context.state.pending_notification(GRACE)
    assert due.version == "2026.4.1"
    assert due.episode == 1


def test_an_update_that_is_gone_stops_being_due(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    module.on_message(None, context, availability_message(context, message, "false"))

    assert context.state.pending_notification(GRACE) is None


def test_availability_returning_opens_a_new_episode(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))
    context.state.mark_notified(1)

    module.on_message(None, context, availability_message(context, message, "false"))
    module.on_message(None, context, version_message(context, message, "2026.4.2"))
    module.on_message(None, context, availability_message(context, message, "true"))

    due = context.state.pending_notification(GRACE)
    assert due.episode == 2
    assert due.version == "2026.4.2"


def test_the_version_of_a_finished_episode_is_not_reused(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    module.on_message(None, context, availability_message(context, message, "false"))

    assert context.state.current_version() is None


def test_a_repeated_availability_message_changes_nothing(module, context, message):
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))
    context.state.mark_notified(1)

    module.on_message(None, context, availability_message(context, message, "true"))

    assert context.state.pending_notification(GRACE) is None


def test_a_damaged_availability_payload_is_ignored(module, context, message, caplog):
    """Reading anything but true/false as false would end the episode."""
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    with caplog.at_level(logging.WARNING):
        module.on_message(
            None, context, availability_message(context, message, "unavailable")
        )

    assert context.state.pending_notification(GRACE).version == "2026.4.1"
    assert context.state.current_version() == "2026.4.1"
    assert "unexpected payload" in caplog.text


@pytest.mark.parametrize("payload", ["True", "TRUE", "1", "", "yes", "unavailable"])
def test_only_the_exact_payloads_are_accepted(module, context, message, payload):
    """Tested during a running episode: an empty state cannot tell ignoring
    apart from reading the value as false, both would look the same."""
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    module.on_message(None, context, availability_message(context, message, payload))

    due = context.state.pending_notification(GRACE)
    assert due.episode == 1
    assert due.version == "2026.4.1"


@pytest.mark.parametrize(
    "topic_of",
    [
        lambda config: config.update_available_topic,
        lambda config: config.update_version_topic,
    ],
)
def test_an_undecodable_payload_is_ignored(module, context, message, caplog, topic_of):
    """Raising here would end paho's network loop, not just this message."""
    module.on_message(None, context, version_message(context, message, "2026.4.1"))
    module.on_message(None, context, availability_message(context, message, "true"))

    with caplog.at_level(logging.WARNING):
        module.on_message(None, context, message(topic_of(context.config), b"\xff\xfe"))

    due = context.state.pending_notification(GRACE)
    assert due.episode == 1
    assert due.version == "2026.4.1"
    assert "undecodable payload of 2 bytes" in caplog.text


def test_ignores_unrelated_topics(module, context, message):
    module.on_message(None, context, message("teslamate/cars/1/battery_level", "42"))

    assert context.state.current_version() is None
    assert context.state.pending_notification(GRACE) is None


def test_contexts_do_not_leak_into_each_other(module, config, message):
    """Two cars, two contexts: neither the topics nor the state are shared."""
    first = module.MqttCallbackContext(config=config, state=module.State())
    second_config = module.Config(
        car_id=2,
        namespace="garage",
        mqtt_host=config.mqtt_host,
        mqtt_port=config.mqtt_port,
        mqtt_username=config.mqtt_username,
        mqtt_password=config.mqtt_password,
        telegram_token=config.telegram_token,
        telegram_chat_id=config.telegram_chat_id,
    )
    second = module.MqttCallbackContext(config=second_config, state=module.State())

    assert first.config.update_version_topic != second.config.update_version_topic

    module.on_message(None, first, version_message(first, message, "2026.4.1"))

    assert first.state.current_version() == "2026.4.1"
    assert second.state.current_version() is None
