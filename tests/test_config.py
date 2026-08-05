"""Tests for reading the configuration.

The settings are taken as one snapshot at startup. Importing the module reads
nothing, so these tests arrange an environment and call from_env() rather than
re-importing anything.
"""

import importlib
import os

import pytest

import teslamate_telegram_bot as bot

REQUIRED = {"TELEGRAM_BOT_API_KEY": "token", "TELEGRAM_BOT_CHAT_ID": "42"}


@pytest.fixture(name="clean_env")
def fixture_clean_env(monkeypatch):
    """Only what a test sets is in the environment."""
    for name in (
        "CAR_ID",
        "MQTT_NAMESPACE",
        "MQTT_BROKER_HOST",
        "MQTT_BROKER_PORT",
        "MQTT_BROKER_USERNAME",
        "MQTT_BROKER_PASSWORD",
        *REQUIRED,
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in REQUIRED.items():
        monkeypatch.setenv(name, value)


@pytest.mark.usefixtures("clean_env")
def test_falls_back_to_the_documented_defaults(module):
    config = module.Config.from_env()

    assert config.car_id == module.CAR_ID_DEFAULT
    assert config.namespace == module.MQTT_NAMESPACE_DEFAULT
    assert config.mqtt_host == module.MQTT_BROKER_HOST_DEFAULT
    assert config.mqtt_port == module.MQTT_BROKER_PORT_DEFAULT
    assert config.mqtt_username == module.MQTT_BROKER_USERNAME_DEFAULT
    assert config.mqtt_password == module.MQTT_BROKER_PASSWORD_DEFAULT


@pytest.mark.usefixtures("clean_env")
def test_reads_every_setting(module, monkeypatch):
    monkeypatch.setenv("CAR_ID", "7")
    monkeypatch.setenv("MQTT_NAMESPACE", "garage")
    monkeypatch.setenv("MQTT_BROKER_HOST", "broker.local")
    monkeypatch.setenv("MQTT_BROKER_PORT", "8883")
    monkeypatch.setenv("MQTT_BROKER_USERNAME", "user")
    monkeypatch.setenv("MQTT_BROKER_PASSWORD", "secret")

    config = module.Config.from_env()

    assert config.car_id == 7
    assert config.namespace == "garage"
    assert config.mqtt_host == "broker.local"
    assert config.mqtt_port == 8883
    assert config.mqtt_username == "user"
    assert config.mqtt_password == "secret"
    assert config.telegram_token == "token"
    assert config.telegram_chat_id == 42


@pytest.mark.usefixtures("clean_env")
def test_topics_address_the_configured_car(module, monkeypatch):
    monkeypatch.setenv("CAR_ID", "7")

    config = module.Config.from_env()

    assert config.update_version_topic == "teslamate/cars/7/update_version"
    assert config.update_available_topic == "teslamate/cars/7/update_available"


@pytest.mark.usefixtures("clean_env")
def test_topics_carry_the_namespace(module, monkeypatch):
    monkeypatch.setenv("MQTT_NAMESPACE", "garage")

    config = module.Config.from_env()

    assert config.update_available_topic == "teslamate/garage/cars/1/update_available"


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("CAR_ID", "not-a-car"),
        ("MQTT_BROKER_PORT", "not-a-port"),
        ("TELEGRAM_BOT_CHAT_ID", "not-a-chat"),
    ],
)
@pytest.mark.usefixtures("clean_env")
def test_names_the_setting_that_is_not_a_number(module, monkeypatch, variable, value):
    monkeypatch.setenv(variable, value)

    with pytest.raises(OSError, match=variable):
        module.Config.from_env()


@pytest.mark.parametrize("variable", ["TELEGRAM_BOT_API_KEY", "TELEGRAM_BOT_CHAT_ID"])
@pytest.mark.usefixtures("clean_env")
def test_names_the_setting_that_is_missing(module, monkeypatch, variable):
    monkeypatch.delenv(variable)

    with pytest.raises(OSError, match=variable):
        module.Config.from_env()


@pytest.mark.usefixtures("clean_env")
def test_is_a_snapshot(module, monkeypatch):
    """Later changes to the environment do not reach a config already read."""
    monkeypatch.setenv("MQTT_BROKER_HOST", "broker.local")
    config = module.Config.from_env()

    monkeypatch.setenv("MQTT_BROKER_HOST", "somewhere.else")

    assert config.mqtt_host == "broker.local"


def test_keeps_the_secrets_out_of_its_repr(config):
    """A config in a traceback or a debug line must not carry credentials."""
    shown = repr(config)

    assert config.telegram_token not in shown
    assert config.mqtt_password not in shown
    assert "broker.local" in shown  # the harmless parts are still there


def test_the_module_imports_with_an_unusable_setting(monkeypatch):
    """Reading at startup instead of at import: a bad value is main()'s
    problem, not something that breaks the import."""
    monkeypatch.setenv("CAR_ID", "not-a-car")

    importlib.reload(bot)

    assert os.getenv("CAR_ID") == "not-a-car"
