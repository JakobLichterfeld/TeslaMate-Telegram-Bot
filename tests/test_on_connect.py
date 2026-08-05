"""Tests for the MQTT connect and subscribe callbacks."""

import logging

import pytest

MQTT_ERR_SUCCESS = 0


class RecordingClient:
    """Records the topics the callback subscribes to.

    subscribe() answers like paho's: a result code and the message id the
    SUBACK will refer to.
    """

    def __init__(self, result=MQTT_ERR_SUCCESS):
        self.subscribed = []
        self.result = result

    def subscribe(self, topic):
        self.subscribed.append(topic)
        return self.result, len(self.subscribed)


def test_subscribes_to_both_topics_after_a_successful_connect(module, context):
    client = RecordingClient()

    module.on_connect(client, context, None, 0)

    assert client.subscribed == [
        context.config.update_available_topic,
        context.config.update_version_topic,
    ]


def test_a_subscription_is_only_requested_here_not_granted(module, context):
    """The broker answers with a SUBACK; until then nothing is confirmed."""
    module.on_connect(RecordingClient(), context, None, 0)

    assert context.status.subscriptions_ready() is False
    assert context.status.subscription_failure() is None


def test_reports_a_subscribe_request_that_could_not_be_sent(module, context, caplog):
    """A client that cannot even ask must not leave the bot waiting."""
    client = RecordingClient(result=4)  # MQTT_ERR_NO_CONN

    with caplog.at_level(logging.ERROR):
        module.on_connect(client, context, None, 0)

    assert context.status.subscription_failure() is not None
    assert client.subscribed == [context.config.update_available_topic]  # stopped
    assert "Could not request a subscription" in caplog.text


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

    assert context.status.connection_failure() == reason_code
    assert client.subscribed == []


def test_a_successful_connect_reports_no_failure(module, context):
    module.on_connect(RecordingClient(), context, None, 0)

    assert context.status.connection_failure() is None


class ReasonCode:
    """Stands in for paho's ReasonCode, which is what on_subscribe receives."""

    def __init__(self, is_failure, text):
        self.is_failure = is_failure
        self.text = text

    def __str__(self):
        return self.text


def test_a_granted_subscription_makes_the_bot_ready(module, context):
    module.on_connect(RecordingClient(), context, None, 0)

    module.on_subscribe(None, context, 1, [ReasonCode(False, "Granted QoS 0")])
    module.on_subscribe(None, context, 2, [ReasonCode(False, "Granted QoS 0")])

    assert context.status.subscriptions_ready() is True
    assert context.status.subscription_failure() is None


def test_the_bot_is_not_ready_until_every_suback_arrived(module, context):
    module.on_connect(RecordingClient(), context, None, 0)

    module.on_subscribe(None, context, 1, [ReasonCode(False, "Granted QoS 0")])

    assert context.status.subscriptions_ready() is False


def test_a_refused_subscription_is_reported(module, context, caplog):
    """An ACL may allow the connection and still forbid the topic."""
    module.on_connect(RecordingClient(), context, None, 0)

    with caplog.at_level(logging.ERROR):
        module.on_subscribe(None, context, 1, [ReasonCode(True, "Not authorized")])

    assert context.status.subscription_failure() == "Not authorized"
    assert context.status.subscriptions_ready() is False
    assert "refused a subscription" in caplog.text


def test_a_reconnect_starts_the_subscriptions_over(module, context):
    """A connection dropping between SUBSCRIBE and SUBACK leaves ids behind.

    Kept, they would make the next attempt wait for answers that can never
    arrive and time the start out.
    """
    module.on_connect(RecordingClient(), context, None, 0)  # first attempt, no SUBACK

    client = RecordingClient()
    module.on_connect(client, context, None, 0)  # reconnect asks again
    module.on_subscribe(None, context, 1, [ReasonCode(False, "Granted QoS 0")])
    module.on_subscribe(None, context, 2, [ReasonCode(False, "Granted QoS 0")])

    assert context.status.subscriptions_ready() is True
