# MIT License
#
# Copyright (c) 2024 mhand

"""Tests for the GET /api/v1/dograh/call-state read route and the
WebModeServer dograh_call_state broadcast wiring.

The dograh client is mocked; the route reads the in-memory holder.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.integrations.dograh_call_state import (
    CALL_STATE_IN_CALL,
    CALL_STATE_RINGING,
    CALL_STATE_UNKNOWN,
    DograhCallState,
    get_call_state_holder,
)
from chatty_commander.web.routes.dograh import router


@pytest.fixture(autouse=True)
def _reset_holder():
    # Keep the process-wide singleton clean across tests.
    get_call_state_holder().set(DograhCallState())
    yield
    get_call_state_holder().set(DograhCallState())


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestCallStateRoute:
    def test_default_is_unknown(self):
        r = _client().get("/api/v1/dograh/call-state")
        assert r.status_code == 200
        body = r.json()
        assert body == {"state": "unknown", "workflow_id": None, "run_id": None}

    def test_reflects_holder(self):
        get_call_state_holder().set(
            DograhCallState(CALL_STATE_RINGING, workflow_id=4, run_id=8)
        )
        r = _client().get("/api/v1/dograh/call-state")
        body = r.json()
        assert body == {"state": "ringing", "workflow_id": 4, "run_id": 8}


class TestBroadcastWiring:
    """The poller's on-change callback updates the holder and broadcasts a
    `dograh_call_state` message — NOT a `state_change`."""

    @pytest.mark.asyncio
    async def test_on_dograh_call_state_updates_holder_and_broadcasts(self):
        from chatty_commander.web.web_mode import WebModeServer

        # Build a server with light fakes; we only exercise the callback.
        server = WebModeServer.__new__(WebModeServer)
        broadcast: list = []

        async def fake_broadcast(msg):
            broadcast.append(msg)

        server._broadcast_message = fake_broadcast  # type: ignore[assignment]

        snap = DograhCallState(CALL_STATE_IN_CALL, workflow_id=2, run_id=3)
        await server._on_dograh_call_state(snap)

        # Holder updated.
        assert get_call_state_holder().get().state == CALL_STATE_IN_CALL
        # Exactly one broadcast, of the dedicated type (not state_change).
        assert len(broadcast) == 1
        msg = broadcast[0]
        assert msg.type == "dograh_call_state"
        assert msg.data == {
            "state": "in_call",
            "workflow_id": 2,
            "run_id": 3,
        }

    @pytest.mark.asyncio
    async def test_start_poller_wires_callback_and_broadcasts_on_change(self):
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

        poller = server.start_dograh_call_poller(
            FakeClient(), workflow_id=1, run_id=1
        )
        try:
            changed = await poller.poll_once()
            assert changed is True
            assert len(broadcast) == 1
            assert broadcast[0].type == "dograh_call_state"
            assert broadcast[0].data["state"] == CALL_STATE_RINGING
        finally:
            await server.stop_dograh_call_poller()

    @pytest.mark.asyncio
    async def test_default_server_has_no_active_poller(self):
        # Dormant by default: no run registered -> holder stays unknown.
        assert get_call_state_holder().get().state == CALL_STATE_UNKNOWN
