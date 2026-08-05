"""Tests for wiring up the MQTT client."""

import types

import pytest


class RecordingClient:
    """Stands in for paho's client and records how it was configured."""

    def __init__(self, callback_api_version, userdata=None):
        self.callback_api_version = callback_api_version
        self.userdata = userdata
        self.credentials = None
        self.connected_to = None
        self.on_connect = None
        self.on_message = None

    def username_pw_set(self, username, password):
        self.credentials = (username, password)

    def connect(self, host, port, keepalive):
        self.connected_to = (host, port, keepalive)


@pytest.fixture(name="fake_mqtt")
def fixture_fake_mqtt(module, monkeypatch):
    """Replace the paho module so no socket is opened."""
    created = []

    def client(callback_api_version, userdata=None):
        created.append(RecordingClient(callback_api_version, userdata))
        return created[-1]

    monkeypatch.setattr(
        module,
        "mqtt",
        types.SimpleNamespace(
            Client=client,
            CallbackAPIVersion=types.SimpleNamespace(VERSION2="v2"),
        ),
    )
    return created


def test_hands_the_context_to_the_client_as_user_data(module, context, fake_mqtt):
    client = module.setup_mqtt_client(context)

    assert fake_mqtt == [client]
    assert client.userdata is context
    assert client.callback_api_version == "v2"


@pytest.mark.usefixtures("fake_mqtt")
def test_registers_both_callbacks(module, context):
    client = module.setup_mqtt_client(context)

    assert client.on_connect is module.on_connect
    assert client.on_message is module.on_message


@pytest.mark.usefixtures("fake_mqtt")
def test_connects_to_the_configured_broker(module, context):
    """Everything comes from the config, nothing is read again here."""
    client = module.setup_mqtt_client(context)

    assert client.credentials == ("user", "secret")
    assert client.connected_to == (
        "broker.local",
        1883,
        module.MQTT_BROKER_KEEPALIVE,
    )
