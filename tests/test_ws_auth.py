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

"""Handshake authentication for the WebSocket endpoints.

``AuthMiddleware`` is a Starlette ``BaseHTTPMiddleware`` and never sees the
WebSocket scope, so ``/ws``, ``/avatar/ws`` and ``/ws/voice-test`` would be
unauthenticated. ``authorize_websocket`` (``web/routes/ws.py``) re-applies the
project's auth model at the handshake, mirroring the HTTP degradation rule:

* user auth INACTIVE (``--no-auth`` / no users / no JWT secret) → pass-through;
* user auth ACTIVE → a valid JWT *access* token via the ``?token=`` query
  parameter (what the frontend already sends) is required, else the handshake
  is rejected (close code 1008, policy violation).
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest

try:
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from fastapi import FastAPI

from chatty_commander.web.deps.auth import (
    JWT_ALGORITHM,
    configure_auth_context,
    get_auth_context,
)
from chatty_commander.web.routes.ws import WS_POLICY_VIOLATION, include_ws_routes
from chatty_commander.web.server import create_app

SECRET = "ws-auth-test-secret"


def _token(*, secret: str = SECRET, jti: str = "ws-jti", roles=None) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "alice",
            "roles": roles or ["user"],
            "type": "access",
            "jti": jti,
            "iat": now,
            "exp": now + 600,
        },
        secret,
        algorithm=JWT_ALGORITHM,
    )


def _active_config() -> SimpleNamespace:
    """A config_manager making user auth ACTIVE (users + JWT secret)."""
    return SimpleNamespace(
        model_actions={
            "screenshot": {"action": "keypress", "keys": "ctrl+shift+x"},
        },
        auth={
            "users": {"alice": {"password_hash": "x", "roles": ["user"]}},
            "jwt_secret": SECRET,
        },
    )


@pytest.fixture(autouse=True)
def _isolate_auth_context(monkeypatch):
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)
    monkeypatch.delenv("CHATTY_API_KEY", raising=False)
    get_auth_context().reset()
    yield
    get_auth_context().reset()


def _build_app(path: str, *, no_auth: bool, config: SimpleNamespace) -> FastAPI:
    """Build an app exposing ``path``.

    ``/avatar/ws`` and ``/ws/voice-test`` are wired by ``create_app`` via
    ``register_shared_routers`` (which also calls ``configure_auth_context``).
    ``/ws`` is provided only by the ``web_mode`` factory, so for it we build a
    minimal app from ``include_ws_routes`` and configure the auth context the
    same way ``register_shared_routers`` does.
    """
    if path == "/ws":
        app = FastAPI()
        app.include_router(
            include_ws_routes(
                get_connections=lambda: set(),
                set_connections=lambda conns: None,
                get_state_snapshot=lambda: {"current_state": "idle"},
            )
        )
        configure_auth_context(config_manager=config, no_auth=no_auth)
        return app
    return create_app(no_auth=no_auth, config_manager=config)


# ── auth ACTIVE: credential required ────────────────────────────────────────


@pytest.mark.parametrize("path", ["/ws", "/avatar/ws", "/ws/voice-test"])
def test_ws_rejected_without_credential_when_auth_active(path: str):
    app = _build_app(path, no_auth=False, config=_active_config())
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(path):
            pass
    assert exc.value.code == WS_POLICY_VIOLATION


@pytest.mark.parametrize("path", ["/ws", "/avatar/ws", "/ws/voice-test"])
def test_ws_rejected_with_invalid_credential_when_auth_active(path: str):
    app = _build_app(path, no_auth=False, config=_active_config())
    client = TestClient(app)
    bad = _token(secret="not-the-server-secret")
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"{path}?token={bad}"):
            pass
    assert exc.value.code == WS_POLICY_VIOLATION


@pytest.mark.parametrize("path", ["/ws", "/avatar/ws", "/ws/voice-test"])
def test_ws_accepted_with_valid_credential_when_auth_active(path: str):
    app = _build_app(path, no_auth=False, config=_active_config())
    client = TestClient(app)
    with client.websocket_connect(f"{path}?token={_token()}") as ws:
        # A successful handshake delivers an initial server frame on every
        # endpoint (snapshot / connection_established); voice-test only emits
        # after a client frame, so we drive it explicitly.
        if path == "/ws/voice-test":
            ws.send_json({"type": "text", "text": "screenshot"})
            assert ws.receive_json()["stage"] == "transcript"
        else:
            assert ws.receive_json()["type"] in (
                "connection_established",
                "agent_states_snapshot",
            )


# ── auth INACTIVE (no-auth): open, no credential needed ─────────────────────


@pytest.mark.parametrize("path", ["/ws", "/avatar/ws", "/ws/voice-test"])
def test_ws_accepted_without_credential_in_no_auth_mode(path: str):
    app = _build_app(path, no_auth=True, config=_active_config())
    client = TestClient(app)
    with client.websocket_connect(path) as ws:
        if path == "/ws/voice-test":
            ws.send_json({"type": "text", "text": "screenshot"})
            assert ws.receive_json()["stage"] == "transcript"
        else:
            assert ws.receive_json()["type"] in (
                "connection_established",
                "agent_states_snapshot",
            )


def test_ws_open_when_no_users_configured_even_with_api_key():
    """No ``auth.users`` ⇒ user auth inactive ⇒ pass-through (matches the
    existing ``/ws/voice-test`` middleware-bypass test's config shape)."""
    cfg = SimpleNamespace(
        model_actions={"screenshot": {"action": "keypress", "keys": "ctrl+shift+x"}},
        auth={"api_key": "sekrit"},  # api_key alone does not activate user auth
    )
    app = create_app(no_auth=False, config_manager=cfg)
    client = TestClient(app)
    with client.websocket_connect("/ws/voice-test") as ws:
        ws.send_json({"type": "start", "dry_run": True})
        assert ws.receive_json()["stage"] == "listening"
