"""Tests for Phase-2 role-based access (AUTHZ_DESIGN.md §4).

Covers ``web/deps/auth.py``: the ``Principal`` model, ``current_principal``,
the ``require_role`` dependency, and the ``AuthContext`` degradation rule. The
crux is the additive/opt-in contract: a server in ``--no-auth`` mode, or with
no ``auth.users`` configured, treats ``require_role`` as a *pass-through*
(allow), NOT a 401/403 — so existing flows are byte-for-byte unchanged. Roles
are only enforced when user auth is actually active AND a Bearer token is
present.

These tests exercise both the dependency in isolation and the two guarded
endpoints wired in ``web/routes/core.py`` (PUT /api/v1/config → admin,
POST /api/v1/command → user) end-to-end via the real ``create_app`` factory.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest

try:
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.deps.auth import (
    ANONYMOUS,
    JWT_ALGORITHM,
    ROLE_RANK,
    Principal,
    configure_auth_context,
    current_principal,
    get_auth_context,
    require_role,
)
from chatty_commander.web.revocation import InMemoryRevocationStore

SECRET = "phase2-test-secret"


def _token(roles: list[str], *, secret: str = SECRET, jti: str = "jti-1") -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "alice",
            "roles": roles,
            "type": "access",
            "jti": jti,
            "iat": now,
            "exp": now + 600,
        },
        secret,
        algorithm=JWT_ALGORITHM,
    )


def _active_config(roles: list[str] | None = None) -> SimpleNamespace:
    """A config_manager that makes user auth *active* (users + secret)."""
    return SimpleNamespace(
        auth={
            "users": {"alice": {"password_hash": "x", "roles": roles or ["user"]}},
            "jwt_secret": SECRET,
        }
    )


@pytest.fixture(autouse=True)
def _isolate_context(monkeypatch):
    """Reset the process-wide singleton + clear the env secret per test."""
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)
    get_auth_context().reset()
    yield
    get_auth_context().reset()


def _guarded_app(store=None) -> FastAPI:
    app = FastAPI()

    @app.get("/read")
    def _read():
        return {"ok": True}

    @app.post("/cmd", dependencies=[Depends(require_role("user"))])
    def _cmd():
        return {"ok": True}

    @app.put("/cfg", dependencies=[Depends(require_role("admin"))])
    def _cfg():
        return {"ok": True}

    return app


def _client(store=None) -> TestClient:
    return TestClient(_guarded_app(store), raise_server_exceptions=False)


# ── ROLE_RANK / Principal unit ──────────────────────────────────────────────


def test_role_rank_ordering():
    assert ROLE_RANK == {"readonly": 0, "user": 1, "admin": 2}


def test_principal_max_rank_picks_highest_known_role():
    assert Principal(sub="a", roles=["readonly", "admin"]).max_rank == 2
    assert Principal(sub="a", roles=["user"]).max_rank == 1
    # Unknown roles are ignored, not crashed on.
    assert Principal(sub="a", roles=["bogus"]).max_rank == -1
    assert Principal(sub="a", roles=[]).max_rank == -1


def test_anonymous_sentinel_is_flagged():
    assert ANONYMOUS.anonymous is True
    assert ANONYMOUS.roles == []


def test_require_role_rejects_unknown_minimum():
    with pytest.raises(ValueError):
        require_role("superuser")


# ── degradation rule: auth INACTIVE => pass-through (the crux) ──────────────


def test_passthrough_when_no_config_manager():
    # Default singleton: no config_manager => auth inactive => allow.
    assert get_auth_context().is_auth_active() is False
    c = _client()
    assert c.post("/cmd").status_code == 200
    assert c.put("/cfg").status_code == 200


def test_passthrough_when_no_users_configured():
    # config present but no auth.users => feature off => allow (no 401/403).
    configure_auth_context(
        config_manager=SimpleNamespace(auth={"jwt_secret": SECRET}), no_auth=False
    )
    assert get_auth_context().is_auth_active() is False
    c = _client()
    assert c.post("/cmd").status_code == 200
    assert c.put("/cfg").status_code == 200


def test_passthrough_in_no_auth_mode_even_with_users():
    # --no-auth wins: roles never enforced even if users + secret exist.
    configure_auth_context(config_manager=_active_config(["readonly"]), no_auth=True)
    assert get_auth_context().is_auth_active() is False
    c = _client()
    # A readonly principal would normally be 403 on /cmd, but no_auth bypasses.
    assert c.post("/cmd").status_code == 200
    assert c.put("/cfg").status_code == 200
    # ... and no token at all is also fine.
    assert (
        c.post("/cmd", headers={"Authorization": "Bearer nonsense"}).status_code == 200
    )


def test_passthrough_when_users_but_no_jwt_secret():
    # Users configured but no resolvable secret => can't have issued a token
    # => treat as inactive and allow (don't hard-fail the request path).
    configure_auth_context(
        config_manager=SimpleNamespace(auth={"users": {"a": {}}}), no_auth=False
    )
    assert get_auth_context().is_auth_active() is False
    c = _client()
    assert c.post("/cmd").status_code == 200


# ── auth ACTIVE => enforce ──────────────────────────────────────────────────


def test_active_sufficient_role_allowed():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    assert get_auth_context().is_auth_active() is True
    c = _client()
    r = c.post("/cmd", headers={"Authorization": f"Bearer {_token(['user'])}"})
    assert r.status_code == 200


def test_active_admin_allowed_on_admin_route():
    configure_auth_context(config_manager=_active_config(["admin"]), no_auth=False)
    c = _client()
    r = c.put("/cfg", headers={"Authorization": f"Bearer {_token(['admin'])}"})
    assert r.status_code == 200


def test_active_insufficient_role_403():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    # user role on an admin-only route => 403 (authenticated but not enough).
    r = c.put("/cfg", headers={"Authorization": f"Bearer {_token(['user'])}"})
    assert r.status_code == 403
    # readonly on a user route => 403.
    r2 = c.post("/cmd", headers={"Authorization": f"Bearer {_token(['readonly'])}"})
    assert r2.status_code == 403


def test_active_missing_token_401():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    assert c.post("/cmd").status_code == 401


def test_active_malformed_header_401():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    assert c.post("/cmd", headers={"Authorization": "Token abc"}).status_code == 401


def test_active_invalid_signature_401():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    bad = _token(["admin"], secret="wrong-secret")
    assert c.post("/cmd", headers={"Authorization": f"Bearer {bad}"}).status_code == 401


def test_active_expired_token_401():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    now = int(time.time())
    expired = jwt.encode(
        {
            "sub": "alice",
            "roles": ["admin"],
            "type": "access",
            "jti": "x",
            "iat": now - 3600,
            "exp": now - 1800,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    r = c.post("/cmd", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_active_wrong_token_type_401():
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    now = int(time.time())
    refresh = jwt.encode(
        {"sub": "alice", "type": "refresh", "jti": "r", "iat": now, "exp": now + 600},
        SECRET,
        algorithm=JWT_ALGORITHM,
    )
    r = c.post("/cmd", headers={"Authorization": f"Bearer {refresh}"})
    assert r.status_code == 401


def test_active_revoked_token_401():
    # The dependency consults the SAME revocation store it is configured with.
    store = InMemoryRevocationStore()
    configure_auth_context(
        config_manager=_active_config(["admin"]),
        no_auth=False,
        revocation_store=store,
    )
    c = _client()
    token = _token(["admin"], jti="revoke-me")
    # Works before revocation.
    assert (
        c.put("/cfg", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    )
    # Revoke its jti; now the same token is rejected with 401.
    store.revoke("revoke-me", int(time.time()) + 600)
    assert (
        c.put("/cfg", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    )


def test_unguarded_route_unaffected_when_active():
    # A route WITHOUT require_role keeps working with no token even when auth
    # is active (the middleware, not require_role, is the coarse gate).
    configure_auth_context(config_manager=_active_config(["user"]), no_auth=False)
    c = _client()
    assert c.get("/read").status_code == 200


# ── current_principal called directly ───────────────────────────────────────


def test_current_principal_returns_anonymous_when_inactive():
    # Inactive => sentinel regardless of header value.
    p = current_principal(authorization="Bearer whatever")
    assert p.anonymous is True
    assert p.sub is None


def test_current_principal_resolves_roles_when_active():
    configure_auth_context(config_manager=_active_config(["admin"]), no_auth=False)
    p = current_principal(authorization=f"Bearer {_token(['admin', 'user'])}")
    assert p.anonymous is False
    assert p.sub == "alice"
    assert set(p.roles) == {"admin", "user"}
