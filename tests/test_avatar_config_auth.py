"""Auth gating for the config-persisting PUT /avatar/config endpoint.

PUT /avatar/config persists configuration but lives outside the /api/ prefix
that AuthMiddleware gates, so without an explicit dependency it would be
reachable unauthenticated (the same hole previously fixed for /avatar/launch).
It now declares require_role("user"), which enforces an authenticated user when
auth is active and is a pass-through otherwise (web/deps/auth.py degradation
rule).
"""

from __future__ import annotations

import time

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
from chatty_commander.web.server import create_app

SECRET = "avatar-config-secret"


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
    yield
    get_auth_context().reset()


def _active_client() -> TestClient:
    # The avatar_settings router (which owns /avatar/config) is registered only
    # by server.create_app and only when a config_manager is supplied.
    cfg = Config(config_file="")
    cfg.config["auth"] = {
        "jwt_secret": SECRET,
        "users": {"alice": {"password_hash": "x", "roles": ["user"]}},
    }
    app = create_app(config_manager=cfg, no_auth=True)
    # Re-configure to no_auth=False so the require_role gate is active while the
    # coarse X-API-Key middleware (bypassed by no_auth=True at build) stays out.
    configure_auth_context(config_manager=cfg, no_auth=False)
    assert get_auth_context().is_auth_active() is True
    return TestClient(app, raise_server_exceptions=False)


def test_put_avatar_config_requires_auth_when_active():
    """No Bearer token => 401 when user auth is active."""
    client = _active_client()
    resp = client.put("/avatar/config", json={"enabled": False})
    assert resp.status_code == 401


def test_put_avatar_config_allowed_with_user_token():
    client = _active_client()
    resp = client.put(
        "/avatar/config",
        json={"enabled": False},
        headers={"Authorization": f"Bearer {_token(['user'])}"},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_put_avatar_config_passthrough_in_no_auth_mode():
    """--no-auth (no users configured) => guard is a pass-through, no 401."""
    cfg = Config(config_file="")
    app = create_app(config_manager=cfg, no_auth=True)
    assert get_auth_context().is_auth_active() is False
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.put("/avatar/config", json={"enabled": True})
    assert resp.status_code == 200


def test_get_avatar_config_unaffected_when_active():
    """The read path carries no role guard and stays reachable."""
    client = _active_client()
    resp = client.get("/avatar/config")
    assert resp.status_code == 200
    assert "enabled" in resp.json()
