"""Tests for reading environment variables."""

import pytest


def test_returns_the_value_from_the_environment(module, monkeypatch):
    monkeypatch.setenv("MQTT_BROKER_HOST", "broker.local")

    assert module.get_env_variable("MQTT_BROKER_HOST", "127.0.0.1") == "broker.local"


def test_falls_back_to_the_default(module, monkeypatch):
    monkeypatch.delenv("MQTT_BROKER_HOST", raising=False)

    assert module.get_env_variable("MQTT_BROKER_HOST", "127.0.0.1") == "127.0.0.1"


def test_returns_none_for_an_unset_optional_variable(module, monkeypatch):
    monkeypatch.delenv("MQTT_NAMESPACE", raising=False)

    assert module.get_env_variable("MQTT_NAMESPACE") is None


@pytest.mark.parametrize("var_name", ["TELEGRAM_BOT_API_KEY", "TELEGRAM_BOT_CHAT_ID"])
def test_raises_for_a_required_variable(module, monkeypatch, var_name):
    monkeypatch.delenv(var_name, raising=False)

    with pytest.raises(OSError, match=var_name):
        module.get_env_variable(var_name)
