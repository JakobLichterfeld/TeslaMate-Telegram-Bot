"""Tests for the MQTT message callback.

The state arrives as paho's user data, so every test can hand in its own.
"""


def test_stores_the_announced_version(module, state, message):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )

    assert state.current_version() == "2026.4.1"


def test_marks_an_update_as_available(module, state, message):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "true")
    )

    assert state.pending_update() == "2026.4.1"


def test_an_update_that_is_gone_stops_being_pending(module, state, message):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "true")
    )

    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "false")
    )

    assert state.pending_update() is None


def test_the_same_version_is_not_reported_again_after_it_reappears(
    module, state, message
):
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "true")
    )
    state.mark_notified("2026.4.1")

    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "false")
    )
    module.on_message(
        None, state, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE, "true")
    )

    assert state.pending_update() is None


def test_ignores_unrelated_topics(module, state, message):
    module.on_message(None, state, message("teslamate/cars/1/battery_level", "42"))

    assert state.current_version() == "unknown"
    assert state.pending_update() is None


def test_states_do_not_leak_into_each_other(module, message):
    first, second = module.State(), module.State()

    module.on_message(
        first, first, message(module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION, "2026.4.1")
    )

    assert first.current_version() == "2026.4.1"
    assert second.current_version() == "unknown"
