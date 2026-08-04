"""Tests for the MQTT message callback.

The state arrives as paho's user data, so every test can hand in its own.
"""


def test_stores_the_announced_version(module, state, message):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )

    assert state.update_version == "2026.4.1"


def test_marks_an_update_as_available(module, state, message):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "true")
    )

    assert state.update_available is True


def test_clears_the_sent_flag_when_the_update_is_gone(module, state, message):
    state.update_available_message_sent = True

    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "false")
    )

    assert state.update_available is False
    assert state.update_available_message_sent is False


def test_ignores_unrelated_topics(module, state, message):
    module.on_message(None, state, message("teslamate/cars/1/battery_level", "42"))

    assert state.update_version == "unknown"
    assert state.update_available is False


def test_states_do_not_leak_into_each_other(module, message):
    first, second = module.State(), module.State()

    module.on_message(
        first, first, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )

    assert first.update_version == "2026.4.1"
    assert second.update_version == "unknown"
