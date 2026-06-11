"""Phase 1 token-lifecycle tests (AUTHZ_DESIGN.md §2/§3).

Covers refresh tokens, rotation, and the jti revocation denylist layered on top
of the minimal login shipped in #678. Time is mocked where needed (no real
sleeps). The back-compat / opt-in contract is reasserted with named tests so a
server with no auth config and/or --no-auth stays byte-for-byte unchanged.
"""

from __future__ import annotations

import time
from unittest.mock import Mock

import bcrypt
import jwt
import pytest

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.revocation import InMemoryRevocationStore
from chatty_commander.web.routes.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    JWT_ALGORITHM,
    REFRESH_TOKEN_TTL_SECONDS,
    include_auth_routes,
)

SECRET = "test-jwt-secret"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _users():
    return {"alice": {"password_hash": _hash("s3cret"), "roles": ["admin", "user"]}}


def _config(users=_users, jwt_secret: str | None = SECRET) -> Mock:
    auth: dict = {}
    resolved = users() if callable(users) else users
    if resolved is not None:
        auth["users"] = resolved
    if jwt_secret is not None:
        auth["jwt_secret"] = jwt_secret
    cfg = Mock()
    cfg.auth = auth
    return cfg


def _client(config_manager, store=None) -> TestClient:
    app = FastAPI()
    app.include_router(
        include_auth_routes(
            get_config_manager=lambda: config_manager, revocation_store=store
        )
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _no_env_secret(monkeypatch):
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)


def _login(client) -> dict:
    resp = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert resp.status_code == 200
    return resp.json()


# ── login now issues access + refresh ──────────────────────────────────────


def test_login_returns_access_and_refresh_tokens():
    client = _client(_config())
    body = _login(client)
    # Back-compat fields plus the additive refresh_token.
    assert {"access_token", "token_type", "expires_in", "refresh_token"} <= set(body)
    access = jwt.decode(body["access_token"], SECRET, algorithms=[JWT_ALGORITHM])
    refresh = jwt.decode(body["refresh_token"], SECRET, algorithms=[JWT_ALGORITHM])
    assert access["type"] == "access"
    assert refresh["type"] == "refresh"
    # Each token carries its own jti, iat, exp, sub (design §2).
    for claims in (access, refresh):
        assert claims["sub"] == "alice"
        assert isinstance(claims["jti"], str) and claims["jti"]
        assert "iat" in claims and "exp" in claims
    assert access["jti"] != refresh["jti"]
    # Refresh is the longer-lived token.
    assert refresh["exp"] - refresh["iat"] == REFRESH_TOKEN_TTL_SECONDS
    assert access["exp"] - access["iat"] == ACCESS_TOKEN_TTL_SECONDS


# ── refresh issues a new access token ───────────────────────────────────────


def test_refresh_issues_new_access_token():
    client = _client(_config())
    refresh_token = _login(client)["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    new_access = jwt.decode(body["access_token"], SECRET, algorithms=[JWT_ALGORITHM])
    assert new_access["type"] == "access"
    assert new_access["sub"] == "alice"
    assert new_access["roles"] == ["admin", "user"]
    # The new access token works against /me.
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200


# ── refresh rotates + revokes the old refresh jti ───────────────────────────


def test_refresh_rotates_and_revokes_old_refresh_token():
    client = _client(_config())
    first_refresh = _login(client)["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert resp.status_code == 200
    second_refresh = resp.json()["refresh_token"]
    assert second_refresh != first_refresh

    # Old refresh token is now revoked (single-use rotation).
    replay = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first_refresh}
    )
    assert replay.status_code == 401

    # The freshly issued refresh token still works.
    again = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second_refresh}
    )
    assert again.status_code == 200


# ── logout revokes the access jti ───────────────────────────────────────────


def test_logout_revokes_access_token_jti():
    client = _client(_config())
    tokens = _login(client)
    access = tokens["access_token"]
    auth_header = {"Authorization": f"Bearer {access}"}

    # Works before logout.
    assert client.get("/api/v1/auth/me", headers=auth_header).status_code == 200

    assert client.post("/api/v1/auth/logout", headers=auth_header).status_code == 200

    # Same access token is now rejected.
    assert client.get("/api/v1/auth/me", headers=auth_header).status_code == 401


def test_logout_also_revokes_refresh_token_when_supplied():
    client = _client(_config())
    tokens = _login(client)
    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 200
    # The revoked refresh token can no longer be used to refresh.
    replay = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401


def test_logout_succeeds_without_token():
    # Logout never fails the client even with no/expired token to revoke.
    client = _client(_config())
    assert client.post("/api/v1/auth/logout").status_code == 200


# ── revoked / expired / wrong-type tokens rejected ──────────────────────────


def test_revoked_refresh_token_rejected():
    store = InMemoryRevocationStore()
    client = _client(_config(), store=store)
    refresh_token = _login(client)["refresh_token"]
    claims = jwt.decode(refresh_token, SECRET, algorithms=[JWT_ALGORITHM])
    store.revoke(claims["jti"], claims["exp"])
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


def test_refresh_rejects_access_token_wrong_type():
    client = _client(_config())
    access = _login(client)["access_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


def test_refresh_rejects_expired_token():
    client = _client(_config())
    now = int(time.time())
    expired = jwt.encode(
        {
            "sub": "alice",
            "type": "refresh",
            "jti": "expired-jti",
            "iat": now - REFRESH_TOKEN_TTL_SECONDS,
            "exp": now - 3600,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": expired})
    assert resp.status_code == 401


def test_refresh_rejects_tampered_signature():
    client = _client(_config())
    refresh_token = _login(client)["refresh_token"]
    tampered = refresh_token[:-2] + ("aa" if refresh_token[-2:] != "aa" else "bb")
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tampered})
    assert resp.status_code == 401


def test_error_detail_does_not_leak_which_check_failed():
    # Wrong-type and bad-signature both surface the same coarse message (§7).
    client = _client(_config())
    access = _login(client)["access_token"]
    wrong_type = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    bad_sig = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not.a.jwt"}
    )
    assert wrong_type.json()["detail"] == bad_sig.json()["detail"] == "Invalid token"


# ── opt-in: endpoints 404 when no users configured (default / --no-auth) ────


def test_refresh_404_when_no_users_configured():
    # No auth.users => feature off; refresh 404s like login/me/logout so the
    # default and --no-auth flows are unchanged.
    client = _client(_config(users=None))
    resp = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "anything"}
    )
    assert resp.status_code == 404


def test_all_endpoints_404_when_no_users_configured_default_unchanged():
    client = _client(_config(users=None))
    assert client.post(
        "/api/v1/auth/login", json={"username": "a", "password": "b"}
    ).status_code == 404
    assert client.get("/api/v1/auth/me").status_code == 404
    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "x"}
    ).status_code == 404
    assert client.post("/api/v1/auth/logout").status_code == 404


def test_no_auth_no_config_manager_endpoints_404():
    # Mirrors the --no-auth / no-config server: nothing configured => 404.
    client = _client(None)
    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "x"}
    ).status_code == 404
