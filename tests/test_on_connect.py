"""Tests for the MQTT connect callback."""

import pytest


class RecordingClient:
    """Records the topics the callback subscribes to."""

    def __init__(self):
        self.subscribed = []

    def subscribe(self, topic):
        self.subscribed.append(topic)


def test_subscribes_to_both_topics_after_a_successful_connect(module, state):
    client = RecordingClient()

    module.on_connect(client, state, None, 0)

    assert client.subscribed == [
        module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE,
        module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION,
    ]


@pytest.mark.parametrize(
    "reason_code",
    [
        "Unsupported protocol version",
        "Client identifier not valid",
        "Not authorized",
        1,
    ],
)
def test_reports_a_rejected_connection_to_the_state(module, state, reason_code):
    """The callback runs in paho's thread, so it must not end the bot itself."""
    client = RecordingClient()

    module.on_connect(client, state, None, reason_code)

    assert state.connection_failure() == reason_code
    assert client.subscribed == []


def test_a_successful_connect_reports_no_failure(module, state):
    module.on_connect(RecordingClient(), state, None, 0)

    assert state.connection_failure() is None
