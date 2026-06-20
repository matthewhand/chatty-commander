# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Coverage tests for the generic /ws router (``include_ws_routes``).

Exercises the full WebSocket lifecycle wired by
``chatty_commander.web.routes.ws.include_ws_routes``:

  * client connect -> ``accept`` + connection registration + initial snapshot
  * inbound JSON dispatch through the ``on_message`` callback
  * non-JSON frames being wrapped as ``{"type": "raw", ...}``
  * ping -> pong symmetry
  * the heartbeat (``TimeoutError``) branch via a tiny ``heartbeat_seconds``
  * broadcast to multiple connected clients (shared connection set)
  * disconnect cleanup (connection removed from the shared set)

The router is mounted on a minimal ``FastAPI`` app via the public factory so the
real ASGI WebSocket lifecycle runs under starlette's ``TestClient``.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from chatty_commander.web.routes.ws import include_ws_routes


class _Harness:
    """Owns the shared connection set + state snapshot for a mounted /ws router."""

    def __init__(self, snapshot: dict | None = None, heartbeat_seconds: float = 30.0):
        self.connections: set[WebSocket] = set()
        self.snapshot = snapshot if snapshot is not None else {"current_state": "idle"}
        self.received: list[dict] = []
        self.app = FastAPI()
        self.app.include_router(
            include_ws_routes(
                get_connections=lambda: self.connections,
                set_connections=self._set_connections,
                get_state_snapshot=lambda: self.snapshot,
                on_message=self.received.append,
                heartbeat_seconds=heartbeat_seconds,
            )
        )

    def _set_connections(self, conns: set[WebSocket]) -> None:
        self.connections = conns

    def client(self) -> TestClient:
        return TestClient(self.app)


@pytest.fixture
def harness() -> _Harness:
    return _Harness()


def test_connect_sends_initial_snapshot(harness: _Harness):
    with harness.client().websocket_connect("/ws") as ws:
        msg = ws.receive_json()
    assert msg["type"] == "connection_established"
    assert msg["data"] == {"current_state": "idle"}
    # timestamp present and ISO-ish (datetime.now().isoformat())
    assert isinstance(msg["timestamp"], str)
    assert "T" in msg["timestamp"]


def test_connect_registers_then_cleans_up_connection(harness: _Harness):
    # During the session the connection set holds exactly one socket.
    with harness.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # drain snapshot
        assert len(harness.connections) == 1
    # After the context exits (client disconnect) the finally-block discards it.
    assert harness.connections == set()


def test_inbound_json_message_dispatched_to_on_message(harness: _Harness):
    with harness.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        ws.send_text(json.dumps({"type": "command", "data": {"name": "go"}}))
        # Round-trip a ping afterwards to be sure the prior frame was processed.
        ws.send_text(json.dumps({"type": "ping"}))
        pong = ws.receive_json()
    assert pong["type"] == "pong"
    assert {"type": "command", "data": {"name": "go"}} in harness.received


def test_non_json_frame_wrapped_as_raw(harness: _Harness):
    with harness.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        ws.send_text("this is not json{")
        # Force synchronization with a ping/pong.
        ws.send_text(json.dumps({"type": "ping"}))
        ws.receive_json()
    raw_msgs = [m for m in harness.received if m.get("type") == "raw"]
    assert raw_msgs and raw_msgs[0]["data"] == "this is not json{"


def test_ping_yields_pong_with_timestamp(harness: _Harness):
    with harness.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        ws.send_text(json.dumps({"type": "ping"}))
        pong = ws.receive_json()
    assert pong["type"] == "pong"
    assert "timestamp" in pong["data"]


def test_non_ping_message_yields_no_response(harness: _Harness):
    """A normal (non-ping) frame is dispatched but produces no reply frame."""
    with harness.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        ws.send_text(json.dumps({"type": "noop"}))
        # Next thing we receive must be the pong, not a reply to "noop".
        ws.send_text(json.dumps({"type": "ping"}))
        nxt = ws.receive_json()
    assert nxt["type"] == "pong"


def test_on_message_none_is_tolerated():
    """When no on_message callback is supplied the loop still processes frames."""
    conns: set[WebSocket] = set()
    app = FastAPI()
    app.include_router(
        include_ws_routes(
            get_connections=lambda: conns,
            set_connections=lambda c: None,
            get_state_snapshot=lambda: {"current_state": "idle"},
            on_message=None,
        )
    )
    with TestClient(app).websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        ws.send_text(json.dumps({"type": "ping"}))
        assert ws.receive_json()["type"] == "pong"


def test_heartbeat_emitted_on_receive_timeout():
    """A tiny heartbeat interval forces the TimeoutError branch to fire."""
    h = _Harness(heartbeat_seconds=0.05)
    with h.client().websocket_connect("/ws") as ws:
        ws.receive_json()  # snapshot
        # We send nothing, so receive_text times out and a heartbeat is pushed.
        beat = ws.receive_json()
    assert beat["type"] == "heartbeat"
    assert "timestamp" in beat["data"]


def test_multiple_clients_share_connection_set(harness: _Harness):
    """Two simultaneous clients are both registered in the shared set.

    The shared, externally-readable connection set is exactly what a broadcaster
    iterates over; here we assert both live sockets are present and independently
    serviceable (each gets its own snapshot + pong).
    """
    client = harness.client()
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect(
        "/ws"
    ) as ws_b:
        snap_a = ws_a.receive_json()
        snap_b = ws_b.receive_json()
        assert snap_a["type"] == snap_b["type"] == "connection_established"
        assert len(harness.connections) == 2
        # Each connection is the genuine starlette WebSocket a broadcaster uses.
        assert all(isinstance(c, WebSocket) for c in harness.connections)

        # Both clients independently serviceable through the same router.
        for ws in (ws_a, ws_b):
            ws.send_text(json.dumps({"type": "ping"}))
            assert ws.receive_json()["type"] == "pong"

    # Both connections cleaned up on disconnect.
    assert harness.connections == set()


def test_disconnect_cleanup_with_concurrent_clients(harness: _Harness):
    client = harness.client()
    with client.websocket_connect("/ws") as ws_a:
        ws_a.receive_json()
        with client.websocket_connect("/ws") as ws_b:
            ws_b.receive_json()
            assert len(harness.connections) == 2
        # ws_b closed; its finally-block discards it, ws_a remains.
        # Sync ws_a so its loop has cycled at least once after ws_b left.
        ws_a.send_text(json.dumps({"type": "ping"}))
        assert ws_a.receive_json()["type"] == "pong"
        assert len(harness.connections) == 1
    assert harness.connections == set()


class _FakeWebSocket:
    """Minimal in-memory WebSocket double driving the endpoint coroutine directly.

    Used for the error/heartbeat branches where starlette's synchronous
    ``TestClient`` deadlocks on a server that returns mid-stream (the server
    endpoint catches everything and returns, but TestClient blocks forever on the
    pending receive). Driving the coroutine directly runs the *real* loop body —
    accept, snapshot send, receive dispatch, the generic ``except`` branch, and
    the ``finally`` cleanup — with no transport portal involved.
    """

    def __init__(self, inbound: list[str]):
        self.accepted = False
        self._inbound = list(inbound)
        self.sent: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, text: str) -> None:
        self.sent.append(text)

    async def receive_text(self) -> str:
        if self._inbound:
            return self._inbound.pop(0)
        # No more scripted frames: emulate the client going away.
        from starlette.websockets import WebSocketDisconnect

        raise WebSocketDisconnect(code=1000)


def _endpoint(router):
    return router.routes[0].endpoint


def test_on_message_exception_does_not_drop_connection():
    """A raising on_message must NOT tear down the connection.

    The callback failure is caught locally (logged + continue), so the loop
    keeps processing subsequent frames — here a follow-up ping still gets its
    pong — and only the eventual client disconnect ends the session.
    """
    conns: set[WebSocket] = set()
    state: dict = {"conns": conns}

    def _set(c):
        state["conns"] = c

    def _boom(_msg: dict) -> None:
        raise RuntimeError("on_message blew up")

    router = include_ws_routes(
        get_connections=lambda: state["conns"],
        set_connections=_set,
        get_state_snapshot=lambda: {"current_state": "idle"},
        on_message=_boom,
    )
    # First frame makes on_message raise; the second (ping) must still be
    # serviced, proving the connection survived the callback failure.
    fake = _FakeWebSocket(
        inbound=[json.dumps({"type": "anything"}), json.dumps({"type": "ping"})]
    )

    import asyncio

    asyncio.run(_endpoint(router)(fake))  # type: ignore[arg-type]

    assert fake.accepted is True
    types = [json.loads(s)["type"] for s in fake.sent]
    # Snapshot was sent before the failing frame was processed.
    assert types[0] == "connection_established"
    # The ping AFTER the raising frame was still handled → loop did not abort.
    assert "pong" in types
    # Connection was registered then discarded on the eventual disconnect.
    assert state["conns"] == set()


def test_websocket_disconnect_branch_cleans_up_connection():
    """Client disconnect mid-receive hits the WebSocketDisconnect handler."""
    state: dict = {"conns": set()}

    def _set(c):
        state["conns"] = c

    router = include_ws_routes(
        get_connections=lambda: state["conns"],
        set_connections=_set,
        get_state_snapshot=lambda: {"current_state": "idle"},
        on_message=None,
    )
    # One ping (gets a pong) then the fake raises WebSocketDisconnect.
    fake = _FakeWebSocket(inbound=[json.dumps({"type": "ping"})])

    import asyncio

    asyncio.run(_endpoint(router)(fake))  # type: ignore[arg-type]

    types = [json.loads(s)["type"] for s in fake.sent]
    assert types[0] == "connection_established"
    assert "pong" in types  # ping handled before the disconnect
    assert state["conns"] == set()  # finally cleaned up


def test_on_message_exception_is_logged(caplog):
    """A raising on_message is logged (not silently swallowed), at DEBUG."""
    import asyncio
    import logging

    state: dict = {"conns": set()}

    router = include_ws_routes(
        get_connections=lambda: state["conns"],
        set_connections=lambda c: state.__setitem__("conns", c),
        get_state_snapshot=lambda: {"current_state": "idle"},
        on_message=lambda _m: (_ for _ in ()).throw(ValueError("kaboom")),
    )
    fake = _FakeWebSocket(inbound=[json.dumps({"type": "x"})])

    with caplog.at_level(logging.DEBUG, logger="chatty_commander.web.routes.ws"):
        asyncio.run(_endpoint(router)(fake))  # type: ignore[arg-type]

    assert any("on_message callback failed" in rec.message for rec in caplog.records)


def test_state_snapshot_reflects_live_provider():
    """get_state_snapshot is read at connect time, not bound at router build."""
    h = _Harness(snapshot={"current_state": "chatty"})
    h.snapshot = {"current_state": "computer", "active_models": ["a", "b"]}
    with h.client().websocket_connect("/ws") as ws:
        msg = ws.receive_json()
    assert msg["data"] == {"current_state": "computer", "active_models": ["a", "b"]}
