"""Tests for the MQTT connect callback."""

import pytest


class RecordingClient:
    """Records the topics the callback subscribes to."""

    def __init__(self):
        self.subscribed = []

    def subscribe(self, topic):
        self.subscribed.append(topic)


def test_subscribes_to_both_topics_after_a_successful_connect(module, context):
    client = RecordingClient()

    module.on_connect(client, context, None, 0)

    assert client.subscribed == [
        context.config.update_available_topic,
        context.config.update_version_topic,
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
def test_reports_a_rejected_connection_to_the_state(module, context, reason_code):
    """The callback runs in paho's thread, so it must not end the bot itself."""
    client = RecordingClient()

    module.on_connect(client, context, None, reason_code)

    assert context.state.connection_failure() == reason_code
    assert client.subscribed == []


def test_a_successful_connect_reports_no_failure(module, context):
    module.on_connect(RecordingClient(), context, None, 0)

    assert context.state.connection_failure() is None
