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
def test_exits_on_a_rejected_connection(module, state, reason_code):
    client = RecordingClient()

    with pytest.raises(SystemExit) as exit_info:
        module.on_connect(client, state, None, reason_code)

    assert exit_info.value.code == 1
    assert client.subscribed == []
