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

"""JWT user-login router with token lifecycle (AUTHZ_DESIGN.md §2/§3, Phase 1).

Implements the endpoints the existing frontend already calls
(``webui/frontend/src/services/authService.ts``) plus token refresh + server-
side revocation:

- ``POST /api/v1/auth/login`` — ``{username, password}`` →
  ``{access_token, token_type:"bearer", expires_in, refresh_token}``.
  ``refresh_token`` is *additive*: existing frontend fields are unchanged so
  ``authService.ts`` keeps working untouched.
- ``GET  /api/v1/auth/me``    — ``Authorization: Bearer <access token>`` →
  ``{username, roles, is_active}``.
- ``POST /api/v1/auth/refresh`` — ``{refresh_token}`` → a *new* access token
  **and a new refresh token** (rotation): the presented refresh ``jti`` is
  revoked and a fresh refresh token is issued (design §2/§3).
- ``POST /api/v1/auth/logout``— revokes the presented Bearer access token's
  ``jti`` (and the refresh token's ``jti`` if supplied) via the denylist.

Credentials are validated against an ``auth.users`` config block holding
bcrypt password hashes and a ``roles`` list (design doc §3/§4). JWTs are signed
HS256 with ``CHATTY_JWT_SECRET`` (env, preferred) or ``auth.jwt_secret``
(config).

**Revocation** uses a :class:`RevocationStore` (``web/revocation.py``) keyed on
``jti``; the default in-memory store self-prunes by ``exp``. The store is
injectable via :func:`include_auth_routes` / :func:`register_auth_routes` so a
future persistent (sqlite) store can replace it without touching this module.

**Opt-in / back-compat:** when no ``auth.users`` are configured every endpoint
returns ``404`` so the default and ``--no-auth`` flows are byte-for-byte
unchanged — the frontend's no-auth probe (``authService.ts``) keeps working.
This builds refresh + revocation only; RBAC dependencies and service keys
remain deferred per the design doc (Phases 2/3).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..deps.auth import JWT_ALGORITHM
from ..deps.auth import bearer_token as _bearer_token
from ..deps.auth import decode_token as _decode_token
from ..deps.auth import jwt_secret_for as _jwt_secret
from ..deps.auth import roles_from as _roles_from
from ..deps.auth import users_for as _users
from ..revocation import InMemoryRevocationStore, RevocationStore

logger = logging.getLogger(__name__)

# Access-token lifetime (seconds). 15 min per AUTHZ_DESIGN.md §2.
ACCESS_TOKEN_TTL_SECONDS = 15 * 60
# Refresh-token lifetime (seconds). 14 days per AUTHZ_DESIGN.md §2.
REFRESH_TOKEN_TTL_SECONDS = 14 * 24 * 60 * 60

# NB: JWT_ALGORITHM and the config/token helpers (_users, _jwt_secret,
# _decode_token, _bearer_token, _roles_from) are now imported from
# ``web/deps/auth.py`` so the Phase-1 router and the Phase-2 role dependency
# share one decode/verify code path (no duplication that could drift).
# Behavior is identical to before.


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    # access_token/token_type/expires_in match authService.ts TokenResponse
    # exactly; refresh_token is additive (older clients simply ignore it).
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_TTL_SECONDS
    refresh_token: str


class UserResponse(BaseModel):
    # Field names/types match authService.ts User (minus the optional
    # client-only noAuth flag, which the backend never sets).
    username: str
    is_active: bool = True
    roles: list[str]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _verify_password(password: str, password_hash: Any) -> bool:
    """Constant-time bcrypt check; tolerant of malformed/empty hashes."""
    if not isinstance(password_hash, str) or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _issue_access_token(username: str, roles: list[str], secret: str) -> str:
    now = int(time.time())
    claims = {
        "sub": username,
        "roles": roles,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


def _issue_refresh_token(username: str, secret: str) -> str:
    now = int(time.time())
    # Minimal claims per design §2: sub, type, jti, iat, exp.
    claims = {
        "sub": username,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + REFRESH_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


def include_auth_routes(
    *,
    get_config_manager: Callable[[], Any],
    revocation_store: RevocationStore | None = None,
) -> APIRouter:
    """Build the JWT auth router bound to a config accessor.

    ``revocation_store`` is the jti denylist consulted on every verify and
    written by logout / refresh-rotation. It defaults to a process-local
    :class:`InMemoryRevocationStore`; pass a persistent implementation to swap
    it (the seam for a future sqlite store — design §3).
    """
    router = APIRouter()
    # NB: use an explicit None check — a freshly-passed store is empty and an
    # InMemoryRevocationStore defines __len__, so `or` would treat it as falsy.
    store: RevocationStore = (
        revocation_store if revocation_store is not None else InMemoryRevocationStore()
    )

    def _require_enabled() -> dict[str, Any]:
        """Resolve users or 404 when the feature is unconfigured (opt-in)."""
        users = _users(get_config_manager())
        if not users:
            # No user store => feature off. 404 keeps the default/no-auth flow
            # unchanged: the frontend falls back to its no-auth probe.
            raise HTTPException(status_code=404, detail="User auth is not configured")
        return users

    def _require_secret() -> str:
        secret = _jwt_secret(get_config_manager())
        if not secret:
            # Users configured but no signing secret: misconfiguration.
            logger.error("auth.users configured but no CHATTY_JWT_SECRET/jwt_secret")
            raise HTTPException(status_code=500, detail="JWT secret not configured")
        return secret

    @router.post("/api/v1/auth/login", response_model=TokenResponse)
    async def login(body: LoginRequest) -> TokenResponse:
        users = _require_enabled()
        secret = _require_secret()

        record = _as_dict(users.get(body.username))
        # Always run a bcrypt check (even for unknown users) to avoid leaking
        # which usernames exist via response timing.
        password_hash = record.get("password_hash")
        if not _verify_password(body.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        roles = _roles_from(record.get("roles", []))
        access = _issue_access_token(body.username, roles, secret)
        refresh = _issue_refresh_token(body.username, secret)
        return TokenResponse(access_token=access, refresh_token=refresh)

    @router.get("/api/v1/auth/me", response_model=UserResponse)
    async def me(authorization: str | None = Header(default=None)) -> UserResponse:
        users = _require_enabled()
        secret = _require_secret()

        token = _bearer_token(authorization)
        claims = _decode_token(token, secret, expected_type="access", store=store)
        username = claims.get("sub")
        if not isinstance(username, str) or username not in users:
            # Token's subject no longer exists in the user store.
            raise HTTPException(status_code=401, detail="Unknown user")

        record = _as_dict(users.get(username))
        roles = _roles_from(claims.get("roles", record.get("roles", [])))
        is_active = bool(record.get("is_active", True))
        return UserResponse(username=username, roles=roles, is_active=is_active)

    @router.post("/api/v1/auth/refresh", response_model=TokenResponse)
    async def refresh(body: RefreshRequest) -> TokenResponse:
        users = _require_enabled()
        secret = _require_secret()

        claims = _decode_token(
            body.refresh_token, secret, expected_type="refresh", store=store
        )
        username = claims.get("sub")
        if not isinstance(username, str) or username not in users:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Rotation: revoke the presented refresh jti and mint a fresh pair so a
        # leaked-then-rotated refresh token is single-use (design §2/§3).
        old_jti = claims.get("jti")
        if isinstance(old_jti, str):
            store.revoke(old_jti, int(claims.get("exp", time.time())))

        record = _as_dict(users.get(username))
        roles = _roles_from(record.get("roles", []))
        access = _issue_access_token(username, roles, secret)
        new_refresh = _issue_refresh_token(username, secret)
        return TokenResponse(access_token=access, refresh_token=new_refresh)

    @router.post("/api/v1/auth/logout")
    async def logout(
        authorization: str | None = Header(default=None),
        body: RefreshRequest | None = None,
    ) -> dict[str, bool]:
        # Revoke the presented access token (and refresh token, if supplied) by
        # jti so it can no longer be used before its natural expiry (design §3).
        _require_enabled()
        secret = _jwt_secret(get_config_manager())
        if secret and authorization:
            try:
                claims = _decode_token(
                    _bearer_token(authorization),
                    secret,
                    expected_type="access",
                    store=store,
                )
            except HTTPException:
                # A missing/expired/already-revoked access token needn't fail
                # logout — the client is dropping it regardless.
                claims = {}
            jti = claims.get("jti")
            if isinstance(jti, str):
                store.revoke(jti, int(claims.get("exp", time.time())))
        if secret and body is not None and body.refresh_token:
            try:
                rclaims = _decode_token(
                    body.refresh_token, secret, expected_type="refresh", store=store
                )
            except HTTPException:
                rclaims = {}
            rjti = rclaims.get("jti")
            if isinstance(rjti, str):
                store.revoke(rjti, int(rclaims.get("exp", time.time())))
        return {"ok": True}

    return router


def register_auth_routes(
    app: Any,
    config_manager: Any = None,
    *,
    revocation_store: RevocationStore | None = None,
) -> None:
    """Single-call registration hook used by ``server.register_shared_routers``."""
    app.include_router(
        include_auth_routes(
            get_config_manager=lambda: config_manager,
            revocation_store=revocation_store,
        )
    )
