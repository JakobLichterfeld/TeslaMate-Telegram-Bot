"""Tests for the shared application state.

State is written from paho's network thread and read from the asyncio side.
These tests pin the semantics of its accessors; the locking itself is not
observable through this API.
"""


def test_nothing_is_pending_without_an_update(state):
    assert state.pending_update() is None


def test_nothing_is_pending_while_the_version_is_unknown(state):
    state.record_availability(True)

    assert state.pending_update() is None


def test_nothing_is_pending_while_the_version_is_empty(state):
    state.record_version("")
    state.record_availability(True)

    assert state.pending_update() is None


def test_nothing_is_pending_without_availability(state):
    state.record_version("2026.4.1")

    assert state.pending_update() is None


def test_an_announced_update_is_pending(state):
    state.record_version("2026.4.1")
    state.record_availability(True)

    assert state.pending_update() == "2026.4.1"


def test_an_acknowledged_update_is_no_longer_pending(state):
    state.record_version("2026.4.1")
    state.record_availability(True)

    state.mark_notified("2026.4.1")

    assert state.pending_update() is None


def test_a_newer_update_becomes_pending_again(state):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified("2026.4.1")

    state.record_version("2026.4.2")

    assert state.pending_update() == "2026.4.2"


def test_acknowledging_a_stale_version_leaves_the_current_one_pending(state):
    """What was sent is acknowledged, not what happens to be current."""
    state.record_version("2026.4.2")
    state.record_availability(True)

    # The notification that is being acknowledged went out for the older one.
    state.mark_notified("2026.4.1")

    assert state.pending_update() == "2026.4.2"


def test_flapping_availability_does_not_repeat_a_notification(state):
    """The version is the identity of a notification, not the episode."""
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified("2026.4.1")

    state.record_availability(False)
    state.record_availability(True)

    assert state.pending_update() is None


def test_reports_the_current_version_regardless_of_notification(state):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified("2026.4.1")

    assert state.current_version() == "2026.4.1"
    assert state.pending_update() is None


def test_the_fields_are_private(state):
    """Callers must go through the methods, which is where the lock is."""
    assert not hasattr(state, "update_available")
    assert not hasattr(state, "update_available_message_sent")
    assert not hasattr(state, "update_version")
