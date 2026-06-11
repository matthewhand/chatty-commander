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

"""Minimal JWT user-login router (AUTHZ_DESIGN.md §2, Phase 1).

Implements exactly the endpoints the existing frontend already calls
(``webui/frontend/src/services/authService.ts``):

- ``POST /api/v1/auth/login`` — ``{username, password}`` →
  ``{access_token, token_type:"bearer", expires_in}``.
- ``GET  /api/v1/auth/me``    — ``Authorization: Bearer <token>`` →
  ``{username, roles, is_active}``.
- ``POST /api/v1/auth/logout``— stateless no-op (client drops the token).

Credentials are validated against an ``auth.users`` config block holding
bcrypt password hashes and a ``roles`` list (design doc §3/§4). The JWT is
signed HS256 with ``CHATTY_JWT_SECRET`` (env, preferred) or ``auth.jwt_secret``
(config).

**Opt-in / back-compat:** when no ``auth.users`` are configured these endpoints
return ``404`` so the default and ``--no-auth`` flows are byte-for-byte
unchanged — the frontend's no-auth probe (``authService.ts``) keeps working.
This deliberately does NOT build refresh tokens, a revocation denylist, an RBAC
dependency system, or service keys — those remain deferred per the design doc.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Access-token lifetime (seconds). 15 min per AUTHZ_DESIGN.md §2.
ACCESS_TOKEN_TTL_SECONDS = 15 * 60
JWT_ALGORITHM = "HS256"
# Small leeway absorbs minor clock drift on decode (design §7).
JWT_LEEWAY_SECONDS = 30


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    # Field names/types match authService.ts TokenResponse exactly.
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_TTL_SECONDS


class UserResponse(BaseModel):
    # Field names/types match authService.ts User (minus the optional
    # client-only noAuth flag, which the backend never sets).
    username: str
    is_active: bool = True
    roles: list[str]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _auth_config(config_manager: Any) -> dict[str, Any]:
    """Return the ``auth`` config block from either Config shape.

    Mirrors the middleware's dual lookup: ``config_manager.auth`` (DummyConfig
    / test objects) or ``config_manager.config["auth"]`` (real ``Config``).
    """
    if config_manager is None:
        return {}
    # DummyConfig pattern: a plain ``.auth`` dict.
    auth_attr = getattr(config_manager, "auth", None)
    if isinstance(auth_attr, dict):
        return auth_attr
    # Real Config pattern: raw JSON under ``.config["auth"]``.
    cfg = getattr(config_manager, "config", None)
    if isinstance(cfg, dict):
        return _as_dict(cfg.get("auth"))
    return {}


def _users(config_manager: Any) -> dict[str, Any]:
    return _as_dict(_auth_config(config_manager).get("users"))


def _jwt_secret(config_manager: Any) -> str | None:
    """Resolve the JWT signing secret: env preferred, then config."""
    env_secret = os.environ.get("CHATTY_JWT_SECRET")
    if env_secret and env_secret.strip():
        return env_secret
    secret = _auth_config(config_manager).get("jwt_secret")
    return secret if isinstance(secret, str) and secret.strip() else None


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
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


def _decode_access_token(token: str, secret: str) -> dict[str, Any]:
    """Decode + validate an access token; raises 401 on any problem."""
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            leeway=JWT_LEEWAY_SECONDS,
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if claims.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return claims


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    return token.strip()


def include_auth_routes(*, get_config_manager: Callable[[], Any]) -> APIRouter:
    """Build the JWT auth router bound to a config accessor."""
    router = APIRouter()

    def _require_enabled() -> dict[str, Any]:
        """Resolve users or 404 when the feature is unconfigured (opt-in)."""
        users = _users(get_config_manager())
        if not users:
            # No user store => feature off. 404 keeps the default/no-auth flow
            # unchanged: the frontend falls back to its no-auth probe.
            raise HTTPException(status_code=404, detail="User auth is not configured")
        return users

    @router.post("/api/v1/auth/login", response_model=TokenResponse)
    async def login(body: LoginRequest) -> TokenResponse:
        users = _require_enabled()
        cm = get_config_manager()
        secret = _jwt_secret(cm)
        if not secret:
            # Users configured but no signing secret: misconfiguration.
            logger.error("auth.users configured but no CHATTY_JWT_SECRET/jwt_secret")
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        record = _as_dict(users.get(body.username))
        # Always run a bcrypt check (even for unknown users) to avoid leaking
        # which usernames exist via response timing.
        password_hash = record.get("password_hash")
        if not _verify_password(body.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        roles_raw = record.get("roles", [])
        roles = (
            [r for r in roles_raw if isinstance(r, str)]
            if isinstance(roles_raw, list)
            else []
        )
        token = _issue_access_token(body.username, roles, secret)
        return TokenResponse(access_token=token)

    @router.get("/api/v1/auth/me", response_model=UserResponse)
    async def me(authorization: str | None = Header(default=None)) -> UserResponse:
        users = _require_enabled()
        cm = get_config_manager()
        secret = _jwt_secret(cm)
        if not secret:
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        token = _bearer_token(authorization)
        claims = _decode_access_token(token, secret)
        username = claims.get("sub")
        if not isinstance(username, str) or username not in users:
            # Token's subject no longer exists in the user store.
            raise HTTPException(status_code=401, detail="Unknown user")

        record = _as_dict(users.get(username))
        roles_raw = claims.get("roles", record.get("roles", []))
        roles = (
            [r for r in roles_raw if isinstance(r, str)]
            if isinstance(roles_raw, list)
            else []
        )
        is_active = bool(record.get("is_active", True))
        return UserResponse(username=username, roles=roles, is_active=is_active)

    @router.post("/api/v1/auth/logout")
    async def logout() -> dict[str, bool]:
        # Stateless tokens: logout is a client-side token drop. We keep the
        # endpoint so the frontend's logout call always succeeds; server-side
        # revocation (a denylist) is deferred per the design doc.
        _require_enabled()
        return {"ok": True}

    return router


def register_auth_routes(app: Any, config_manager: Any = None) -> None:
    """Single-call registration hook used by ``server.register_shared_routers``."""
    app.include_router(
        include_auth_routes(get_config_manager=lambda: config_manager)
    )
