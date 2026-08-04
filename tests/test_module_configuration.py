"""Tests for the configuration that is read while the module is imported.

The topics are built at import time, so these tests re-import the module with
a prepared environment. The environment is handled without monkeypatch on
purpose: the restoring re-import has to happen while the original values are
already back, and fixture teardown order would not guarantee that.
"""

import contextlib
import importlib
import os

import pytest

import teslamate_telegram_bot as bot


@contextlib.contextmanager
def reimported(**environment):
    """Re-import the module with the given environment, then restore it."""
    previous = {name: os.environ.get(name) for name in environment}
    for name, value in environment.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield importlib.reload(bot)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        importlib.reload(bot)


def test_topics_address_the_configured_car():
    with reimported(CAR_ID="7", MQTT_NAMESPACE=None) as module:
        assert (
            module.TESLAMATE_MQTT_TOPIC_UPDATE_VERSION
            == "teslamate/cars/7/update_version"
        )


def test_topics_default_to_the_first_car():
    with reimported(CAR_ID=None, MQTT_NAMESPACE=None) as module:
        assert (
            module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE
            == "teslamate/cars/1/update_available"
        )


def test_topics_carry_the_namespace():
    with reimported(CAR_ID="1", MQTT_NAMESPACE="garage") as module:
        assert (
            module.TESLAMATE_MQTT_TOPIC_UPDATE_AVAILABLE
            == "teslamate/garage/cars/1/update_available"
        )


def test_rejects_a_car_id_that_is_not_a_number():
    with pytest.raises(OSError, match="CAR_ID"), reimported(CAR_ID="not-a-car"):
        pass
