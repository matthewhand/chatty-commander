# MIT License
#
# Copyright (c) 2024 mhand

"""Tests for the dograh call-state track/untrack routes and the poller
lifecycle registry that wires them to the (otherwise dormant) poller.

No real network and no real sleeps: the dograh client is faked and the
poller is driven via the injectable registry / a manual poll_once.

Contract under test:
    POST /api/v1/dograh/call-state/track   {workflow_id, run_id}
        -> 200 {tracking: true, workflow_id, run_id}  (starts poller)
        -> 503 when dograh is unconfigured
    POST /api/v1/dograh/call-state/untrack
        -> 200 {tracking: false}  (stops poller; safe when not tracking)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.integrations.dograh_call_state import (
    CALL_STATE_RINGING,
    CALL_STATE_UNKNOWN,
    DograhCallState,
    get_call_state_holder,
    get_poller_registry,
)
from chatty_commander.integrations.dograh_client import DograhUnavailableError
from chatty_commander.web.routes.dograh import router


@pytest.fixture(autouse=True)
def _reset_singletons():
    get_call_state_holder().set(DograhCallState())
    get_poller_registry().clear()
    yield
    get_call_state_holder().set(DograhCallState())
    get_poller_registry().clear()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _register_recording_registry() -> dict:
    """Register fake start/stop callables; return a dict recording calls."""
    calls: dict = {"started": [], "stopped": 0}

    def _start(workflow_id: int, run_id: int) -> None:
        calls["started"].append((workflow_id, run_id))

    async def _stop() -> None:
        calls["stopped"] += 1

    get_poller_registry().register(start=_start, stop=_stop)
    return calls


class TestTrackRoute:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_track_starts_poller(self, mock_cls):
        # Configured dograh: probe client constructs fine.
        mock_cls.return_value = MagicMock()
        calls = _register_recording_registry()

        r = _client().post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 7, "run_id": 11},
        )
        assert r.status_code == 200
        assert r.json() == {"tracking": True, "workflow_id": 7, "run_id": 11}
        assert calls["started"] == [(7, 11)]

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_retrack_replaces(self, mock_cls):
        mock_cls.return_value = MagicMock()
        calls = _register_recording_registry()

        c = _client()
        c.post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 1, "run_id": 1},
        )
        r = c.post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 2, "run_id": 2},
        )
        assert r.status_code == 200
        # Both starts recorded; the server-side _track_dograh_run stops the
        # previous poller before starting the next (covered by the e2e test).
        assert calls["started"] == [(1, 1), (2, 2)]

    @patch(
        "chatty_commander.integrations.dograh_client.DograhConfig.from_env",
        side_effect=DograhUnavailableError("DOGRAH_BASE_URL not set"),
    )
    def test_track_503_when_unconfigured(self, _mock, monkeypatch):
        monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
        monkeypatch.delenv("DOGRAH_API_KEY", raising=False)
        # Registry registered, but config check fails first -> 503.
        _register_recording_registry()

        r = _client().post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 1, "run_id": 1},
        )
        assert r.status_code == 503
        assert "DOGRAH_BASE_URL" in r.json()["detail"]

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_track_503_when_no_lifecycle_registered(self, mock_cls):
        # Dograh configured but no WebModeServer registered the lifecycle.
        mock_cls.return_value = MagicMock()
        # Registry intentionally left cleared by the fixture.
        r = _client().post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 1, "run_id": 1},
        )
        assert r.status_code == 503

    def test_track_validates_body(self):
        # Missing run_id -> 422 from pydantic before any work.
        r = _client().post(
            "/api/v1/dograh/call-state/track",
            json={"workflow_id": 1},
        )
        assert r.status_code == 422


class TestUntrackRoute:
    def test_untrack_stops_poller(self):
        calls = _register_recording_registry()
        r = _client().post("/api/v1/dograh/call-state/untrack")
        assert r.status_code == 200
        assert r.json() == {"tracking": False, "workflow_id": None, "run_id": None}
        assert calls["stopped"] == 1

    def test_untrack_does_not_require_dograh_configured(self):
        # No DograhClient patch, no env: untrack never touches the network.
        _register_recording_registry()
        r = _client().post("/api/v1/dograh/call-state/untrack")
        assert r.status_code == 200

    def test_untrack_503_when_no_lifecycle_registered(self):
        r = _client().post("/api/v1/dograh/call-state/untrack")
        assert r.status_code == 503


class TestEndToEndViaServer:
    """Exercise the real WebModeServer poller lifecycle through the registry,
    with a fake DograhClient so no network/sleep occurs."""

    @pytest.mark.asyncio
    async def test_track_polls_and_broadcasts_mapped_state(self):
        from chatty_commander.web.web_mode import WebModeServer

        server = WebModeServer.__new__(WebModeServer)
        server._dograh_call_poller = None
        broadcast: list = []

        async def fake_broadcast(msg):
            broadcast.append(msg)

        server._broadcast_message = fake_broadcast  # type: ignore[assignment]

        class FakeClient:
            def get_workflow_run(self, *_):
                return {"state": "ringing"}

        with patch(
            "chatty_commander.integrations.dograh_client.DograhClient",
            return_value=FakeClient(),
        ):
            await server._track_dograh_run(9, 13)
            poller = server._dograh_call_poller
            assert poller is not None
            try:
                changed = await poller.poll_once()
                assert changed is True
                # Holder + broadcast reflect mapped CC call state.
                snap = get_call_state_holder().get()
                assert snap.state == CALL_STATE_RINGING
                assert snap.workflow_id == 9 and snap.run_id == 13
                assert len(broadcast) == 1
                assert broadcast[0].type == "dograh_call_state"
                assert broadcast[0].data["state"] == CALL_STATE_RINGING
            finally:
                await server.stop_dograh_call_poller()

    @pytest.mark.asyncio
    async def test_retrack_replaces_active_poller(self):
        from chatty_commander.web.web_mode import WebModeServer

        server = WebModeServer.__new__(WebModeServer)
        server._dograh_call_poller = None

        async def fake_broadcast(msg):
            pass

        server._broadcast_message = fake_broadcast  # type: ignore[assignment]

        class FakeClient:
            def get_workflow_run(self, *_):
                return {"state": "ringing"}

        with patch(
            "chatty_commander.integrations.dograh_client.DograhClient",
            return_value=FakeClient(),
        ):
            await server._track_dograh_run(1, 1)
            first = server._dograh_call_poller
            await server._track_dograh_run(2, 2)
            second = server._dograh_call_poller
            try:
                # A new poller object replaced the first; the first was stopped.
                assert first is not second
                assert second is not None
                assert second.current.workflow_id == 2
            finally:
                await server.stop_dograh_call_poller()
                assert server._dograh_call_poller is None

    @pytest.mark.asyncio
    async def test_untrack_safe_when_not_tracking(self):
        from chatty_commander.web.web_mode import WebModeServer

        server = WebModeServer.__new__(WebModeServer)
        server._dograh_call_poller = None
        # No poller active: stop is a clean no-op.
        await server.stop_dograh_call_poller()
        assert server._dograh_call_poller is None
        assert get_call_state_holder().get().state == CALL_STATE_UNKNOWN
