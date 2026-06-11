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

"""Role-based access dependencies (AUTHZ_DESIGN.md §4, Phase 2).

This module adds a *finer, per-route* authorization layer on top of the coarse
global ``AuthMiddleware`` X-API-Key gate. It is **additive and opt-in**: routes
that do not declare a ``require_role(...)`` dependency keep behaving exactly as
before, and even routes that *do* declare one fall back to a pass-through
(allow) unless user auth is actually active.

Shared JWT primitives
----------------------
The Bearer-token decode/verify helpers (``decode_access_token``,
``bearer_token``) and the config accessors (``auth_config``, ``users_for``,
``jwt_secret_for``) live here so that both this module and
``web/routes/auth.py`` (Phase 1) use the *same* code path — no duplicated
decode logic that could drift. ``routes/auth.py`` re-imports them.

The "is auth active?" degradation rule
--------------------------------------
``require_role`` only ever returns 401/403 when **user auth is active**, which
means *all* of:

1. ``auth.users`` is configured (non-empty), AND
2. the server is **not** in ``--no-auth`` mode, AND
3. a JWT signing secret is resolvable (``CHATTY_JWT_SECRET`` env or
   ``auth.jwt_secret`` config) — without it no token could have been issued.

When auth is **not** active the dependency resolves to an anonymous
:data:`ANONYMOUS` principal and *allows* the request (pass-through), so a
server in ``--no-auth`` mode, or with no ``auth.users`` configured, behaves
byte-for-byte as it did before this phase. Only when auth is active does the
dependency enforce: a valid Bearer access token carrying a sufficient role is
required, else 401 (bad/missing/revoked token) or 403 (insufficient role).

How the dependency reaches server state
---------------------------------------
A process-wide :class:`AuthContext` singleton (mirroring the
``get_call_state_holder`` / ``get_poller_registry`` accessor pattern) is
populated by ``server.register_shared_routers`` with ``{config_manager,
no_auth, revocation_store}``. The dependency reads config *live* from it on
each call so test-time/config changes are reflected, and shares the *same*
revocation store as the Phase-1 ``/auth/*`` router so a logout/refresh-revoke
is honored by route guards too.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException, Request

from ..revocation import InMemoryRevocationStore, RevocationStore

# Role ordering (design §4). Higher rank => more privilege.
ROLE_RANK: dict[str, int] = {"readonly": 0, "user": 1, "admin": 2}

JWT_ALGORITHM = "HS256"
# Small leeway absorbs minor clock drift on decode (design §7). Mirrors the
# Phase-1 router constant; kept in lockstep with routes/auth.py.
JWT_LEEWAY_SECONDS = 30


# ── shared config accessors (single source of truth for both modules) ──────


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def auth_config(config_manager: Any) -> dict[str, Any]:
    """Return the ``auth`` config block from either Config shape.

    Mirrors the middleware's dual lookup: ``config_manager.auth`` (DummyConfig
    / test objects) or ``config_manager.config["auth"]`` (real ``Config``).
    """
    if config_manager is None:
        return {}
    auth_attr = getattr(config_manager, "auth", None)
    if isinstance(auth_attr, dict):
        return auth_attr
    cfg = getattr(config_manager, "config", None)
    if isinstance(cfg, dict):
        return _as_dict(cfg.get("auth"))
    return {}


def users_for(config_manager: Any) -> dict[str, Any]:
    return _as_dict(auth_config(config_manager).get("users"))


def jwt_secret_for(config_manager: Any) -> str | None:
    """Resolve the JWT signing secret: env preferred, then config."""
    env_secret = os.environ.get("CHATTY_JWT_SECRET")
    if env_secret and env_secret.strip():
        return env_secret
    secret = auth_config(config_manager).get("jwt_secret")
    return secret if isinstance(secret, str) and secret.strip() else None


def roles_from(raw: Any) -> list[str]:
    return [r for r in raw if isinstance(r, str)] if isinstance(raw, list) else []


# ── shared Bearer-token decode/verify (used by routes/auth.py too) ─────────


def bearer_token(authorization: str | None) -> str:
    """Extract the Bearer credential or raise 401 (missing/malformed)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    return token.strip()


def decode_token(
    token: str,
    secret: str,
    *,
    expected_type: str,
    store: RevocationStore,
) -> dict[str, Any]:
    """Decode + validate a JWT of ``expected_type``; raises 401 on any problem.

    The error ``detail`` is intentionally coarse ("Invalid token") for
    signature/format/type problems so we don't leak *which* check failed
    (design §7). Expiry is reported distinctly because it is non-sensitive and
    lets the client know to refresh.
    """
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
    if claims.get("type") != expected_type:
        # Same coarse message as a bad signature: don't reveal it was the type.
        raise HTTPException(status_code=401, detail="Invalid token")
    jti = claims.get("jti")
    if isinstance(jti, str) and store.is_revoked(jti):
        raise HTTPException(status_code=401, detail="Invalid token")
    return claims


def decode_access_token(
    token: str, secret: str, *, store: RevocationStore
) -> dict[str, Any]:
    """Convenience wrapper: decode + verify an ``access``-type token."""
    return decode_token(token, secret, expected_type="access", store=store)


# ── Principal ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Principal:
    """A resolved request identity: a subject and its roles.

    ``anonymous`` marks the pass-through sentinel returned when user auth is
    not active (the degradation rule). It carries no roles, so any genuine
    enforcement would deny it — but enforcement is skipped entirely for it.
    """

    sub: str | None = None
    roles: list[str] = field(default_factory=list)
    anonymous: bool = False

    @property
    def max_rank(self) -> int:
        return max((ROLE_RANK[r] for r in self.roles if r in ROLE_RANK), default=-1)


#: Sentinel principal returned (and allowed) when user auth is inactive.
ANONYMOUS = Principal(sub=None, roles=[], anonymous=True)


# ── process-wide auth context (mirrors get_poller_registry pattern) ─────────


class AuthContext:
    """Process-wide holder for what the role dependency needs to see.

    Populated by ``server.register_shared_routers`` at app construction with
    the active ``config_manager``, the ``no_auth`` flag, and the *shared*
    revocation store (the same instance the Phase-1 ``/auth/*`` router uses).

    Reads are live: the dependency calls :meth:`is_active` / :meth:`config`
    on every request so that config mutated in tests is reflected.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._config_manager: Any = None
        self._no_auth: bool = False
        self._store: RevocationStore = InMemoryRevocationStore()

    def configure(
        self,
        *,
        config_manager: Any,
        no_auth: bool,
        revocation_store: RevocationStore | None = None,
    ) -> None:
        with self._lock:
            self._config_manager = config_manager
            self._no_auth = bool(no_auth)
            if revocation_store is not None:
                self._store = revocation_store

    def reset(self) -> None:
        """Restore defaults (used by tests to isolate the singleton)."""
        with self._lock:
            self._config_manager = None
            self._no_auth = False
            self._store = InMemoryRevocationStore()

    @property
    def config_manager(self) -> Any:
        with self._lock:
            return self._config_manager

    @property
    def no_auth(self) -> bool:
        with self._lock:
            return self._no_auth

    @property
    def revocation_store(self) -> RevocationStore:
        with self._lock:
            return self._store

    def is_auth_active(self) -> bool:
        """Is *user* (role) auth actually enforced right now?

        True only when ALL hold (the degradation rule, design §6):
        users configured AND not no_auth AND a JWT secret is resolvable.
        """
        if self.no_auth:
            return False
        cfg = self.config_manager
        if not users_for(cfg):
            return False
        return bool(jwt_secret_for(cfg))


# Module-level singleton, mirroring dograh's _HOLDER / _POLLER_REGISTRY.
_AUTH_CONTEXT = AuthContext()


def get_auth_context() -> AuthContext:
    """Return the process-wide :class:`AuthContext`."""
    return _AUTH_CONTEXT


def configure_auth_context(
    *,
    config_manager: Any,
    no_auth: bool,
    revocation_store: RevocationStore | None = None,
) -> None:
    """Populate the singleton (called from ``register_shared_routers``)."""
    _AUTH_CONTEXT.configure(
        config_manager=config_manager,
        no_auth=no_auth,
        revocation_store=revocation_store,
    )


# ── the dependencies ────────────────────────────────────────────────────────


def current_principal(authorization: str | None = Header(default=None)) -> Principal:
    """Resolve a verified :class:`Principal` from a Bearer access token.

    Degradation rule: when user auth is **not** active, return :data:`ANONYMOUS`
    (allow) regardless of headers — the request is handled exactly as before
    Phase 2. When auth **is** active, a valid Bearer access token is required:
    a missing/malformed/expired/revoked/wrong-type token raises 401.
    """
    ctx = get_auth_context()
    if not ctx.is_auth_active():
        return ANONYMOUS

    secret = jwt_secret_for(ctx.config_manager)
    if not secret:  # pragma: no cover - is_auth_active already checked this
        return ANONYMOUS

    token = bearer_token(authorization)
    claims = decode_access_token(token, secret, store=ctx.revocation_store)
    sub = claims.get("sub")
    return Principal(
        sub=sub if isinstance(sub, str) else None,
        roles=roles_from(claims.get("roles", [])),
    )


def require_role(minimum: str) -> Callable[..., Principal]:
    """Build a dependency requiring at least the ``minimum`` role.

    Additive + opt-in: when user auth is not active the underlying
    :func:`current_principal` yields the anonymous sentinel and this guard
    allows it (pass-through). When auth is active, an authenticated principal
    whose highest role rank is below ``minimum`` gets 403; an unauthenticated
    one already failed with 401 inside :func:`current_principal`.
    """
    if minimum not in ROLE_RANK:
        raise ValueError(f"unknown role: {minimum!r}")
    needed = ROLE_RANK[minimum]

    def _dep(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.anonymous:
            # Auth inactive: pass-through (degradation rule).
            return principal
        if principal.max_rank < needed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal

    return _dep


# ── scope-based service-key guard (design §5) ───────────────────────────────


def request_scopes(request: Request) -> list[str] | None:
    """Return the X-API-Key scopes the middleware attached, or ``None``.

    The Phase-3 ``AuthMiddleware`` sets ``request.state.scopes`` to the resolved
    scope list (``["*"]`` for the legacy wildcard key, or a service key's
    configured scopes) only when it actively validated an X-API-Key. ``None``
    means the coarse gate did not run for this request — i.e. ``--no-auth`` mode
    or no API key configured at all — which is the pass-through signal for
    :func:`require_scope` (the same degradation rule as :func:`require_role`).
    """
    scopes = getattr(request.state, "scopes", None)
    if isinstance(scopes, list):
        return [s for s in scopes if isinstance(s, str)]
    return None


def has_scope(scopes: list[str] | None, required: str) -> bool:
    """True if ``scopes`` grants ``required`` (wildcard ``"*"`` satisfies any)."""
    if not scopes:
        return False
    return "*" in scopes or required in scopes


def require_scope(scope: str) -> Callable[..., list[str] | None]:
    """Build a dependency requiring the X-API-Key to carry ``scope``.

    Additive + opt-in, mirroring :func:`require_role`'s degradation rule:

    * When the coarse X-API-Key gate did **not** run (``--no-auth`` mode, or no
      API key configured at all), ``request.state.scopes`` is unset and this
      guard is a **pass-through** — default / ``--no-auth`` flows are unchanged.
    * When the gate **did** run, the request already presented a valid key. The
      wildcard legacy key (scopes ``["*"]``) satisfies any required scope; a
      named service key must list ``scope`` explicitly, else 403.

    Returns the resolved scope list (or ``None`` on the pass-through path) so a
    route can introspect it if needed.
    """

    def _dep(request: Request) -> list[str] | None:
        scopes = request_scopes(request)
        if scopes is None:
            # Coarse gate did not run (no_auth / no key config): pass-through.
            return None
        if not has_scope(scopes, scope):
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return scopes

    return _dep


def soft_principal(authorization: str | None) -> Principal:
    """Resolve a :class:`Principal` *without* hard-failing on a missing token.

    Like :func:`current_principal` but tailored for the role-OR-scope
    composition: when user auth is inactive it returns :data:`ANONYMOUS`; when
    auth is active and **no** ``Authorization`` header is present it *still*
    returns :data:`ANONYMOUS` (so a service-key-only caller is not 401'd before
    the scope axis is consulted). A header that *is* present but malformed /
    expired / revoked / wrong-type still raises 401 — a broken token is an
    error, not a silent fall-through.
    """
    ctx = get_auth_context()
    if not ctx.is_auth_active():
        return ANONYMOUS
    secret = jwt_secret_for(ctx.config_manager)
    if not secret:  # pragma: no cover - is_auth_active already checked this
        return ANONYMOUS
    if not authorization:
        return ANONYMOUS
    claims = decode_access_token(
        bearer_token(authorization), secret, store=ctx.revocation_store
    )
    sub = claims.get("sub")
    return Principal(
        sub=sub if isinstance(sub, str) else None,
        roles=roles_from(claims.get("roles", [])),
    )


def require_role_or_scope(*, role: str, scope: str) -> Callable[..., None]:
    """Build a guard satisfied by EITHER a user ``role`` OR a service ``scope``.

    This is the design §5 composition for machine-facing endpoints that should
    accept both an interactive user (Bearer token carrying ``role``) **and** a
    service-to-service caller (X-API-Key carrying ``scope``). It is strictly
    *more permissive* than the previous bare ``require_role(role)`` guard — any
    request that would have passed before still passes — so it is non-breaking.

    Degradation: if *both* axes are inactive the request is allowed, preserving
    the default / ``--no-auth`` behavior. Otherwise the request must satisfy at
    least one *active* axis, else 403. A missing Bearer token does not 401 here
    (the scope axis may carry the request); a present-but-broken token still
    401s via :func:`soft_principal`.
    """
    if role not in ROLE_RANK:
        raise ValueError(f"unknown role: {role!r}")
    needed = ROLE_RANK[role]

    def _dep(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> None:
        principal = soft_principal(authorization)
        scopes = request_scopes(request)
        role_active = not principal.anonymous
        scope_active = scopes is not None

        # Both axes inactive → pure pass-through (default / --no-auth), allow.
        if not role_active and not scope_active:
            return

        # Otherwise the request must satisfy at least one *active* axis. An
        # inactive axis cannot satisfy (its mechanism issued no credential), so
        # e.g. a readonly Bearer user on a key-less deployment is still denied
        # exactly as require_role("user") would have denied it (non-breaking).
        if role_active and principal.max_rank >= needed:
            return
        if scope_active and has_scope(scopes, scope):
            return
        raise HTTPException(status_code=403, detail="Insufficient role or scope")

    return _dep
