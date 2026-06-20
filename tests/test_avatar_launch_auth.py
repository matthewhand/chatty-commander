"""Auth gating for the state-changing /avatar/launch endpoint.

/avatar/launch spawns a host subprocess and lives outside the /api/ prefix that
AuthMiddleware gates, so without an explicit dependency it would be reachable
unauthenticated. It now declares require_role("user"), which enforces an
authenticated user when auth is active and is a pass-through otherwise (the
web/deps/auth.py degradation rule).
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import jwt
import pytest

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.app.config import Config
from chatty_commander.web.deps.auth import (
    JWT_ALGORITHM,
    configure_auth_context,
    get_auth_context,
)
from chatty_commander.web.routes import avatar_api
from chatty_commander.web.web_mode import create_app

SECRET = "avatar-launch-secret"


def _token(roles: list[str]) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "alice",
            "roles": roles,
            "type": "access",
            "jti": f"jti-{'-'.join(roles)}",
            "iat": now,
            "exp": now + 600,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)
    monkeypatch.delenv("CHATTY_API_KEY", raising=False)
    get_auth_context().reset()
    avatar_api._LAUNCHED_PROCESS = None
    yield
    get_auth_context().reset()
    avatar_api._LAUNCHED_PROCESS = None


def _active_client() -> TestClient:
    cfg = Config(config_file="")
    cfg.config["auth"] = {
        "jwt_secret": SECRET,
        "users": {"alice": {"password_hash": "x", "roles": ["user"]}},
    }
    app = create_app(config=cfg, no_auth=True)
    # Re-configure the context to no_auth=False so role enforcement is active
    # while the coarse X-API-Key middleware (bypassed by no_auth=True at build)
    # stays out of the way — we isolate the require_role gate.
    configure_auth_context(config_manager=cfg, no_auth=False)
    assert get_auth_context().is_auth_active() is True
    return TestClient(app, raise_server_exceptions=False)


def test_launch_requires_auth_when_active():
    """No Bearer token => 401 when user auth is active."""
    client = _active_client()
    resp = client.post("/avatar/launch")
    assert resp.status_code == 401


def test_launch_allowed_with_user_token():
    client = _active_client()
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        proc = AsyncMock()
        proc.pid = 4242
        proc.returncode = None
        mock_subprocess.return_value = proc

        resp = client.post(
            "/avatar/launch",
            headers={"Authorization": f"Bearer {_token(['user'])}"},
        )
    assert resp.status_code == 200
    assert resp.json()["pid"] == 4242


def test_launch_passthrough_in_no_auth_mode():
    """--no-auth (no users configured) => guard is a pass-through, no 401."""
    app = create_app(no_auth=True)
    assert get_auth_context().is_auth_active() is False
    client = TestClient(app, raise_server_exceptions=False)
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        proc = AsyncMock()
        proc.pid = 7
        proc.returncode = None
        mock_subprocess.return_value = proc
        resp = client.post("/avatar/launch")
    assert resp.status_code == 200
