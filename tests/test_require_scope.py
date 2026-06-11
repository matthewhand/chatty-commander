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

"""Phase-3 ``require_scope`` dependency + role-OR-scope composition (§5).

Unit-level: the scope guard behavior in isolation, and the helper predicates.
The simulated ``request.state.scopes`` mirrors what the Phase-3 AuthMiddleware
attaches.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from chatty_commander.web.deps.auth import (
    JWT_ALGORITHM,
    configure_auth_context,
    get_auth_context,
    has_scope,
    request_scopes,
    require_role_or_scope,
    require_scope,
)

SECRET = "scope-test-secret"


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)
    monkeypatch.delenv("CHATTY_API_KEY", raising=False)
    get_auth_context().reset()
    yield
    get_auth_context().reset()


def _req(scopes):
    """A stand-in Request whose ``.state.scopes`` mimics the middleware."""
    state = SimpleNamespace()
    if scopes is not _UNSET:
        state.scopes = scopes
    return SimpleNamespace(state=state)


_UNSET = object()


# ── predicate helpers ───────────────────────────────────────────────────────


def test_has_scope_matching():
    assert has_scope(["status:read", "command:write"], "command:write") is True


def test_has_scope_wildcard():
    assert has_scope(["*"], "anything:goes") is True


def test_has_scope_missing():
    assert has_scope(["status:read"], "command:write") is False


def test_has_scope_none_or_empty():
    assert has_scope(None, "x") is False
    assert has_scope([], "x") is False


def test_request_scopes_unset_is_none():
    assert request_scopes(_req(_UNSET)) is None


def test_request_scopes_reads_state():
    assert request_scopes(_req(["a", "b"])) == ["a", "b"]


# ── require_scope ────────────────────────────────────────────────────────────


def test_require_scope_allows_matching():
    dep = require_scope("command:write")
    assert dep(_req(["command:write"])) == ["command:write"]


def test_require_scope_allows_wildcard():
    dep = require_scope("command:write")
    assert dep(_req(["*"])) == ["*"]


def test_require_scope_forbids_without_scope():
    dep = require_scope("command:write")
    with pytest.raises(HTTPException) as exc:
        dep(_req(["status:read"]))
    assert exc.value.status_code == 403


def test_require_scope_passthrough_when_gate_inactive():
    # No scopes on request.state => coarse gate did not run (no_auth / no key
    # configured) => pass-through (returns None, no raise).
    dep = require_scope("command:write")
    assert dep(_req(_UNSET)) is None


# ── require_role_or_scope composition ────────────────────────────────────────


def _token(roles):
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "u",
            "roles": roles,
            "type": "access",
            "jti": "jti-" + "-".join(roles),
            "iat": now,
            "exp": now + 600,
        },
        SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _activate_role_auth():
    cfg = SimpleNamespace(
        config={
            "auth": {
                "jwt_secret": SECRET,
                "users": {"u": {"password_hash": "x", "roles": ["user"]}},
            }
        }
    )
    configure_auth_context(config_manager=cfg, no_auth=False)
    assert get_auth_context().is_auth_active() is True


def _req2(scopes, authorization=None):
    state = SimpleNamespace()
    if scopes is not _UNSET:
        state.scopes = scopes
    return SimpleNamespace(state=state), authorization


def test_role_or_scope_both_inactive_passthrough():
    # Role auth inactive AND no scopes attached => pure pass-through.
    dep = require_role_or_scope(role="user", scope="command:write")
    req, authz = _req2(_UNSET, None)
    assert dep(req, authz) is None


def test_role_or_scope_allows_sufficient_role():
    _activate_role_auth()
    dep = require_role_or_scope(role="user", scope="command:write")
    req, authz = _req2(_UNSET, f"Bearer {_token(['user'])}")
    assert dep(req, authz) is None  # role axis satisfies


def test_role_or_scope_allows_matching_scope_without_token():
    # Service caller: no Bearer token but an X-API-Key carried command:write.
    # Even with role auth active, the scope axis satisfies and no 401 is raised.
    _activate_role_auth()
    dep = require_role_or_scope(role="user", scope="command:write")
    req, authz = _req2(["command:write"], None)
    assert dep(req, authz) is None


def test_role_or_scope_denies_when_neither_satisfies():
    _activate_role_auth()
    dep = require_role_or_scope(role="user", scope="command:write")
    # readonly role (insufficient) and a non-matching scope.
    req, authz = _req2(["status:read"], f"Bearer {_token(['readonly'])}")
    with pytest.raises(HTTPException) as exc:
        dep(req, authz)
    assert exc.value.status_code == 403


def test_role_or_scope_broken_token_still_401s():
    _activate_role_auth()
    dep = require_role_or_scope(role="user", scope="command:write")
    req, authz = _req2(_UNSET, "Bearer garbage")
    with pytest.raises(HTTPException) as exc:
        dep(req, authz)
    assert exc.value.status_code == 401


def test_require_scope_unknown_role_rejected_for_composition():
    with pytest.raises(ValueError):
        require_role_or_scope(role="superuser", scope="x")
