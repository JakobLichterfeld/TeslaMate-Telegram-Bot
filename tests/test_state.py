"""Tests for the shared application state.

State is written from paho's network thread and read from the asyncio side.
These tests pin the semantics of its accessors; the locking itself is not
observable through this API.

A notification belongs to an availability episode. The version is optional
extra information, held back for a grace period and then given up on.
"""

import pytest

GRACE = 30


@pytest.fixture(name="clock")
def fixture_clock():
    """A hand-cranked clock, so waiting is deterministic and instant."""

    class Clock:
        def __init__(self):
            self.now = 1000.0

        def __call__(self):
            return self.now

        def advance(self, seconds):
            self.now += seconds

    return Clock()


@pytest.fixture(name="state")
def fixture_state(module, clock):
    return module.State(clock=clock)


def test_nothing_is_due_without_an_update(state):
    assert state.pending_notification(GRACE) is None


def test_an_update_with_a_version_is_due_at_once(state):
    state.record_version("2026.4.1")
    state.record_availability(True)

    due = state.pending_notification(GRACE)
    assert due.version == "2026.4.1"
    assert due.episode == 1


def test_an_update_without_a_version_waits_for_the_grace_period(state, clock):
    state.record_availability(True)

    assert state.pending_notification(GRACE) is None

    clock.advance(GRACE - 1)
    assert state.pending_notification(GRACE) is None


def test_an_update_without_a_version_is_due_once_the_wait_is_over(state, clock):
    state.record_availability(True)

    clock.advance(GRACE)

    due = state.pending_notification(GRACE)
    assert due.version is None
    assert due.episode == 1


def test_a_version_arriving_within_the_grace_period_still_makes_it_in(state, clock):
    state.record_availability(True)
    clock.advance(GRACE - 1)

    state.record_version("2026.4.1")

    assert state.pending_notification(GRACE).version == "2026.4.1"


def test_an_acknowledged_episode_is_no_longer_due(state):
    state.record_version("2026.4.1")
    state.record_availability(True)

    state.mark_notified(1)

    assert state.pending_notification(GRACE) is None


def test_a_version_arriving_afterwards_does_not_notify_again(state, clock):
    state.record_availability(True)
    clock.advance(GRACE)
    state.mark_notified(state.pending_notification(GRACE).episode)

    state.record_version("2026.4.1")

    assert state.pending_notification(GRACE) is None


def test_repeated_availability_does_not_open_a_new_episode(state):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified(1)

    state.record_availability(True)

    assert state.pending_notification(GRACE) is None


def test_availability_returning_opens_a_new_episode(state, clock):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified(1)

    state.record_availability(False)
    state.record_availability(True)

    # The version of the previous episode is gone, so the new one waits for
    # its own and is then reported without one.
    assert state.pending_notification(GRACE) is None
    clock.advance(GRACE)
    due = state.pending_notification(GRACE)
    assert due.episode == 2
    assert due.version is None


def test_a_repeated_unavailability_message_keeps_the_new_version(state):
    """Only the transition clears, so a repeated false does not drop it."""
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified(1)
    state.record_availability(False)

    state.record_version("2026.4.2")
    state.record_availability(False)  # retained message, reconnect
    state.record_availability(True)

    assert state.pending_notification(GRACE).version == "2026.4.2"


def test_a_retained_unavailability_at_startup_keeps_the_version(state):
    """Startup order: the version is retained, then availability arrives."""
    state.record_version("2026.4.1")
    state.record_availability(False)
    state.record_availability(True)

    assert state.pending_notification(GRACE).version == "2026.4.1"


def test_the_version_of_a_finished_episode_is_not_reused(state):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified(1)

    state.record_availability(False)

    assert state.current_version() == "unknown"


def test_a_version_published_before_the_new_episode_is_kept(state):
    """TeslaMate announces the version, then flips availability."""
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.mark_notified(1)
    state.record_availability(False)

    state.record_version("2026.4.2")
    state.record_availability(True)

    due = state.pending_notification(GRACE)
    assert due.episode == 2
    assert due.version == "2026.4.2"


def test_acknowledging_a_past_episode_leaves_the_current_one_due(state):
    """What was sent is acknowledged, not whatever episode is current."""
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.record_availability(False)
    state.record_version("2026.4.2")
    state.record_availability(True)

    # The message that is being acknowledged went out for the first episode.
    state.mark_notified(1)

    due = state.pending_notification(GRACE)
    assert due.episode == 2
    assert due.version == "2026.4.2"


def test_nothing_is_due_while_unavailable(state):
    state.record_version("2026.4.1")
    state.record_availability(True)
    state.record_availability(False)

    assert state.pending_notification(GRACE) is None


def test_reports_the_current_version(state):
    state.record_version("2026.4.1")

    assert state.current_version() == "2026.4.1"


def test_the_fields_are_private(state):
    """Callers must go through the methods, which is where the lock is."""
    assert not hasattr(state, "update_available")
    assert not hasattr(state, "update_version")
    assert not hasattr(state, "update_available_message_sent")
