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


@pytest.fixture(name="broker_env")
def fixture_broker_env(monkeypatch):
    monkeypatch.setenv("MQTT_BROKER_HOST", "broker.local")
    monkeypatch.setenv("MQTT_BROKER_PORT", "8883")
    monkeypatch.setenv("MQTT_BROKER_USERNAME", "user")
    monkeypatch.setenv("MQTT_BROKER_PASSWORD", "secret")


@pytest.mark.usefixtures("broker_env")
def test_hands_the_state_to_the_client_as_user_data(module, state, fake_mqtt):
    client = module.setup_mqtt_client(state)

    assert fake_mqtt == [client]
    assert client.userdata is state
    assert client.callback_api_version == "v2"


@pytest.mark.usefixtures("broker_env", "fake_mqtt")
def test_registers_both_callbacks(module, state):
    client = module.setup_mqtt_client(state)

    assert client.on_connect is module.on_connect
    assert client.on_message is module.on_message


@pytest.mark.usefixtures("broker_env", "fake_mqtt")
def test_connects_with_the_configured_broker(module, state):
    client = module.setup_mqtt_client(state)

    assert client.credentials == ("user", "secret")
    assert client.connected_to == ("broker.local", 8883, module.MQTT_BROKER_KEEPALIVE)


@pytest.mark.usefixtures("fake_mqtt")
def test_falls_back_to_the_default_broker(module, state, monkeypatch):
    for name in (
        "MQTT_BROKER_HOST",
        "MQTT_BROKER_PORT",
        "MQTT_BROKER_USERNAME",
        "MQTT_BROKER_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    client = module.setup_mqtt_client(state)

    assert client.credentials == ("", "")
    assert client.connected_to == (
        module.MQTT_BROKER_HOST_DEFAULT,
        module.MQTT_BROKER_PORT_DEFAULT,
        module.MQTT_BROKER_KEEPALIVE,
    )


@pytest.mark.usefixtures("fake_mqtt")
def test_rejects_a_port_that_is_not_a_number(module, state, monkeypatch):
    monkeypatch.setenv("MQTT_BROKER_PORT", "not-a-port")

    with pytest.raises(OSError, match="MQTT_BROKER_PORT"):
        module.setup_mqtt_client(state)
