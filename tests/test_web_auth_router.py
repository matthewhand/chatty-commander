"""Tests for the JWT user-login router (BUG 1, AUTHZ_DESIGN.md §2).

Covers the exact request/response shapes ``authService.ts`` sends and parses:
login -> {access_token, token_type, expires_in}; /me with Bearer -> {username,
roles, is_active}. Also asserts the opt-in contract: with no ``auth.users``
configured the endpoints 404 so the default / --no-auth flows are unchanged.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import Mock

import bcrypt
import jwt
import pytest

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.routes.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    JWT_ALGORITHM,
    include_auth_routes,
)

SECRET = "test-jwt-secret"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _config(users: dict | None = None, jwt_secret: str | None = SECRET) -> Mock:
    auth: dict = {}
    if users is not None:
        auth["users"] = users
    if jwt_secret is not None:
        auth["jwt_secret"] = jwt_secret
    cfg = Mock()
    cfg.auth = auth
    return cfg


def _client(config_manager) -> TestClient:
    app = FastAPI()
    app.include_router(include_auth_routes(get_config_manager=lambda: config_manager))
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _no_env_secret(monkeypatch):
    # Tests drive the secret via config unless they opt into the env path.
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)


def _users():
    return {"alice": {"password_hash": _hash("s3cret"), "roles": ["admin", "user"]}}


# ── login ────────────────────────────────────────────────────────────────


def test_login_valid_credentials_returns_parseable_token():
    client = _client(_config(users=_users()))
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert resp.status_code == 200
    body = resp.json()
    # Shape authService.ts TokenResponse expects.
    assert set(body) == {"access_token", "token_type", "expires_in"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == ACCESS_TOKEN_TTL_SECONDS

    # The token authService stores must decode with the configured secret and
    # carry the roles claim the frontend models.
    claims = jwt.decode(body["access_token"], SECRET, algorithms=[JWT_ALGORITHM])
    assert claims["sub"] == "alice"
    assert claims["roles"] == ["admin", "user"]
    assert claims["type"] == "access"


def test_login_invalid_password_rejected():
    client = _client(_config(users=_users()))
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_login_unknown_user_rejected():
    client = _client(_config(users=_users()))
    resp = client.post(
        "/api/v1/auth/login", json={"username": "nobody", "password": "s3cret"}
    )
    assert resp.status_code == 401


def test_login_env_secret_takes_precedence(monkeypatch):
    monkeypatch.setenv("CHATTY_JWT_SECRET", "env-secret")
    client = _client(_config(users=_users(), jwt_secret="config-secret"))
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert resp.status_code == 200
    # Signed with the env secret, not the config one.
    jwt.decode(resp.json()["access_token"], "env-secret", algorithms=[JWT_ALGORITHM])
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(
            resp.json()["access_token"], "config-secret", algorithms=[JWT_ALGORITHM]
        )


# ── /me ──────────────────────────────────────────────────────────────────


def test_me_with_valid_token_returns_user_shape():
    client = _client(_config(users=_users()))
    token = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    ).json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    # Shape authService.ts User expects.
    assert body == {"username": "alice", "is_active": True, "roles": ["admin", "user"]}


def test_me_missing_token_401():
    client = _client(_config(users=_users()))
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_malformed_header_401():
    client = _client(_config(users=_users()))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401


def test_me_expired_token_401():
    client = _client(_config(users=_users()))
    expired = jwt.encode(
        {
            "sub": "alice",
            "roles": ["admin"],
            "type": "access",
            "iat": int(time.time()) - 3600,
            "exp": int(time.time()) - 1800,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert resp.status_code == 401


def test_me_wrong_token_type_401():
    client = _client(_config(users=_users()))
    refresh = jwt.encode(
        {
            "sub": "alice",
            "type": "refresh",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}
    )
    assert resp.status_code == 401


def test_me_token_for_unknown_subject_401():
    client = _client(_config(users=_users()))
    token = jwt.encode(
        {
            "sub": "ghost",
            "roles": ["admin"],
            "type": "access",
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 401


# ── logout ───────────────────────────────────────────────────────────────


def test_logout_ok_when_enabled():
    client = _client(_config(users=_users()))
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


# ── opt-in / disabled-when-no-users (default + no-auth unchanged) ──────────


def test_endpoints_404_when_no_users_configured():
    # No auth.users => feature off. All three endpoints 404 so the default and
    # --no-auth flows are byte-for-byte unchanged (frontend no-auth probe path).
    client = _client(_config(users=None))
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "a", "password": "b"}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/auth/me").status_code == 404
    assert client.post("/api/v1/auth/logout").status_code == 404


def test_endpoints_404_with_no_config_manager():
    client = _client(None)
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "a", "password": "b"}
        ).status_code
        == 404
    )


def test_login_500_when_users_but_no_secret():
    # Users configured but no signing secret anywhere => clear 500, not a crash.
    client = _client(_config(users=_users(), jwt_secret=None))
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert resp.status_code == 500


def test_real_config_shape_via_config_dict():
    # Exercise the real Config path: auth lives under .config["auth"], no .auth.
    cfg = SimpleNamespace(
        config={"auth": {"users": _users(), "jwt_secret": SECRET}}
    )
    client = _client(cfg)
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert resp.status_code == 200
