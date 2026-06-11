# MIT License
#
# Copyright (c) 2024 mhand

"""Tests for the phase-0 dograh call-state bridge.

Covers state mapping, change detection, poller lifecycle (start/stop/
cancel with no real sleeps), and the in-memory holder. The dograh client
is mocked entirely — no live instance is required.
"""

from __future__ import annotations

import asyncio

import pytest

from chatty_commander.integrations.dograh_call_state import (
    CALL_STATE_ENDED,
    CALL_STATE_IN_CALL,
    CALL_STATE_RINGING,
    CALL_STATE_UNKNOWN,
    DograhCallState,
    DograhCallStateHolder,
    DograhCallStatePoller,
    extract_run_state,
    get_call_state_holder,
    map_dograh_state,
    map_run_record,
)


class _FakeClient:
    """Fake DograhClient: returns scripted run records in sequence."""

    def __init__(self, records: list[dict]) -> None:
        self._records = list(records)
        self.calls = 0

    def get_workflow_run(self, workflow_id: int, run_id: int) -> dict:
        self.calls += 1
        # Return last record forever once exhausted.
        idx = min(self.calls - 1, len(self._records) - 1)
        return self._records[idx]


# --- state mapping -------------------------------------------------------


class TestStateMapping:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("ringing", CALL_STATE_RINGING),
            ("dialing", CALL_STATE_RINGING),
            ("queued", CALL_STATE_RINGING),
            ("in_call", CALL_STATE_IN_CALL),
            ("in-progress", CALL_STATE_IN_CALL),
            ("active", CALL_STATE_IN_CALL),
            ("answered", CALL_STATE_IN_CALL),
            ("ended", CALL_STATE_ENDED),
            ("completed", CALL_STATE_ENDED),
            ("failed", CALL_STATE_ENDED),
            ("cancelled", CALL_STATE_ENDED),
        ],
    )
    def test_known_states_map(self, raw, expected):
        assert map_dograh_state(raw) == expected

    def test_case_and_whitespace_insensitive(self):
        assert map_dograh_state("  RINGING ") == CALL_STATE_RINGING

    def test_unknown_value_maps_to_unknown(self):
        assert map_dograh_state("frobnicating") == CALL_STATE_UNKNOWN

    def test_none_maps_to_unknown(self):
        assert map_dograh_state(None) == CALL_STATE_UNKNOWN

    def test_extract_run_state_probes_candidate_fields(self):
        assert extract_run_state({"state": "ringing"}) == "ringing"
        assert extract_run_state({"status": "active"}) == "active"
        assert extract_run_state({"call_status": "ended"}) == "ended"
        # No candidate field present.
        assert extract_run_state({"unrelated": "x"}) is None
        # Empty value is treated as absent.
        assert extract_run_state({"state": ""}) is None

    def test_map_run_record_end_to_end(self):
        assert map_run_record({"status": "answered"}) == CALL_STATE_IN_CALL
        assert map_run_record({}) == CALL_STATE_UNKNOWN


# --- holder --------------------------------------------------------------


class TestHolder:
    def test_default_is_unknown(self):
        holder = DograhCallStateHolder()
        snap = holder.get()
        assert snap.state == CALL_STATE_UNKNOWN
        assert snap.workflow_id is None
        assert snap.run_id is None

    def test_set_and_get(self):
        holder = DograhCallStateHolder()
        holder.set(DograhCallState(CALL_STATE_IN_CALL, 7, 9))
        assert holder.get().state == CALL_STATE_IN_CALL
        assert holder.get().workflow_id == 7

    def test_module_singleton(self):
        assert get_call_state_holder() is get_call_state_holder()


# --- message shape -------------------------------------------------------


def test_message_data_shape():
    snap = DograhCallState(CALL_STATE_RINGING, workflow_id=3, run_id=11)
    assert snap.as_message_data() == {
        "state": "ringing",
        "workflow_id": 3,
        "run_id": 11,
    }


# --- change detection (poll_once) ----------------------------------------


class TestChangeDetection:
    @pytest.mark.asyncio
    async def test_callback_fires_only_on_transition(self):
        client = _FakeClient(
            [
                {"state": "ringing"},
                {"state": "ringing"},  # no change
                {"state": "in_call"},  # change
            ]
        )
        seen: list[str] = []

        async def on_change(snap: DograhCallState) -> None:
            seen.append(snap.state)

        poller = DograhCallStatePoller(
            client, workflow_id=1, run_id=2, on_change=on_change
        )

        assert await poller.poll_once() is True  # unknown -> ringing
        assert await poller.poll_once() is False  # ringing -> ringing
        assert await poller.poll_once() is True  # ringing -> in_call

        assert seen == [CALL_STATE_RINGING, CALL_STATE_IN_CALL]
        assert poller.current.state == CALL_STATE_IN_CALL

    @pytest.mark.asyncio
    async def test_sync_callback_supported(self):
        client = _FakeClient([{"state": "ringing"}])
        seen: list[str] = []

        poller = DograhCallStatePoller(
            client, 1, 2, on_change=lambda s: seen.append(s.state)
        )
        await poller.poll_once()
        assert seen == [CALL_STATE_RINGING]

    @pytest.mark.asyncio
    async def test_client_error_is_swallowed(self):
        class Boom:
            def get_workflow_run(self, *_):
                raise RuntimeError("dograh down")

        fired: list[str] = []
        poller = DograhCallStatePoller(
            Boom(), 1, 2, on_change=lambda s: fired.append(s.state)
        )
        assert await poller.poll_once() is False
        assert fired == []
        assert poller.current.state == CALL_STATE_UNKNOWN

    @pytest.mark.asyncio
    async def test_callback_error_does_not_crash(self):
        client = _FakeClient([{"state": "ringing"}])

        def boom(_s):
            raise ValueError("callback bug")

        poller = DograhCallStatePoller(client, 1, 2, on_change=boom)
        # Should not raise.
        assert await poller.poll_once() is True
        assert poller.current.state == CALL_STATE_RINGING


# --- poller lifecycle (no real sleeps) -----------------------------------


class TestPollerLifecycle:
    @pytest.mark.asyncio
    async def test_run_stops_at_terminal_state(self):
        client = _FakeClient(
            [
                {"state": "ringing"},
                {"state": "in_call"},
                {"state": "ended"},
            ]
        )
        seen: list[str] = []
        # Injected no-op async sleep: no real seconds elapse.
        slept: list[float] = []

        async def fake_sleep(delay: float) -> None:
            slept.append(delay)

        poller = DograhCallStatePoller(
            client,
            1,
            2,
            on_change=lambda s: seen.append(s.state),
            interval_seconds=5.0,
            sleep=fake_sleep,
        )
        # run() should self-terminate once "ended" is observed.
        await asyncio.wait_for(poller.run(), timeout=1.0)

        assert seen == [
            CALL_STATE_RINGING,
            CALL_STATE_IN_CALL,
            CALL_STATE_ENDED,
        ]
        # Slept between polls but never on the terminal one.
        assert slept == [5.0, 5.0]

    @pytest.mark.asyncio
    async def test_start_and_stop_cancels_loop(self):
        # Never-terminal client: loop runs until cancelled.
        client = _FakeClient([{"state": "in_call"}])

        sleep_started = asyncio.Event()

        async def blocking_sleep(_delay: float) -> None:
            sleep_started.set()
            await asyncio.sleep(3600)  # effectively block until cancelled

        poller = DograhCallStatePoller(
            client,
            1,
            2,
            on_change=lambda s: None,
            sleep=blocking_sleep,
        )
        task = poller.start()
        # Wait until the loop has polled once and is parked in sleep.
        await asyncio.wait_for(sleep_started.wait(), timeout=1.0)
        assert poller.current.state == CALL_STATE_IN_CALL

        await poller.stop()
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_stop_is_safe_when_never_started(self):
        poller = DograhCallStatePoller(
            _FakeClient([{}]), 1, 2, on_change=lambda s: None
        )
        await poller.stop()  # no-op, must not raise

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        client = _FakeClient([{"state": "in_call"}])

        async def block(_d):
            await asyncio.sleep(3600)

        poller = DograhCallStatePoller(
            client, 1, 2, on_change=lambda s: None, sleep=block
        )
        t1 = poller.start()
        t2 = poller.start()
        assert t1 is t2
        await poller.stop()
