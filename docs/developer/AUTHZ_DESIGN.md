# AuthN/AuthZ Depth — Design Proposal

Status: **Draft for owner review.** This is a design document, not an
implementation. No production code or tests are changed by this PR.

ROADMAP item (`docs/developer/AGENT_STEERING.md:40`, "AuthN/AuthZ depth"):
*token refresh + revocation, role-based access (admin/user/readonly),
API-key auth for service-to-service.*

ChattyCommander is a **local-first voice assistant**, not a multi-tenant SaaS.
The design below is deliberately sized to that reality: it deepens auth where
the frontend already expects it, keeps the single-API-key default intact, and
explicitly defers enterprise IdP machinery (see [§8 Overkill](#8-explicitly-overkill-deferred)).

---

## 1. Current auth model (survey)

### What exists today

**A single global API key, enforced by middleware.**
`AuthMiddleware` (`src/chatty_commander/web/middleware/auth.py:38`) is a
Starlette `BaseHTTPMiddleware` that protects everything under `/api`
(`auth.py:95`). It reads a header `X-API-Key` (`auth.py:96`) and compares it
against an expected key using `constant_time_compare`
(`auth.py:119`, `src/chatty_commander/utils/security.py:28`). On mismatch it
returns a flat `401 {"detail": "..."}` (`auth.py:124`).

**Where the expected key comes from.** The middleware looks in two places
(`auth.py:104-116`):
- `config_manager.auth["api_key"]` — used by test/DummyConfig objects.
- `config_manager.config["auth"]["api_key"]` — the real `Config`, whose
  `.config` is just the raw parsed JSON (`src/chatty_commander/app/config.py:48`).

There is **no env var, no schema, and no default** for this key. `Config`
populates `web_server.auth_enabled` (`config.py:313`) and a `bridge_token`
(`config.py:314`) but **never populates an `auth.api_key`** — it only exists if
the user hand-writes `{"auth": {"api_key": "..."}}` into their config file.

**Path-traversal hardening.** The middleware aggressively URL-decodes
(up to 10 rounds) and `posixpath.normpath`s the path before matching exemptions
(`auth.py:65-81`) so `/%2e%2e/api/...` style bypasses are blocked.

**Exemptions.** `/docs`, `/redoc`, `/openapi.json`, `/static`, `/`
(`auth.py:47-57`) and all `OPTIONS` preflight requests (`auth.py:91`).

**The `no_auth` development bypass.** When `no_auth=True` the middleware returns
immediately with no checks (`auth.py:62`). It is threaded from the CLI through
`WebModeServer` (`web/web_mode.py:400`) and `server.create_app` (`server.py:205`).

**Production refusal.** `ensure_no_auth_allowed` (`server.py:128-149`) raises
`RuntimeError` if `no_auth=True` **and** `CHATTY_ENV=production`
(case-insensitive). It is called by *both* app factories
(`server.py:208`, `web/web_mode.py:537`) so neither path can drift.

**Bridge token (separate scheme).** `/bridge/event` uses an `X-Bridge-Token`
header validated against `web_server.bridge_token`
(`web/web_mode.py:889-910`, `server.py:262-309`). Independent of the API key.

**CORS.** `apply_cors` (`src/chatty_commander/web/auth.py:64`) allows
`Authorization`, `X-API-Key`, `X-Bridge-Token` headers (`auth.py:93`), pins
origins to localhost (overridable via `CHATTY_CORS_ORIGINS`,
`web/web_mode.py:606`), and refuses `allow_credentials` with `*` (`auth.py:86`).

**Rate limiting.** Two layers: a coarse per-IP `RateLimitMiddleware`
(`web/web_mode.py:269`) and a per-caller **token bucket** on
`POST /api/v1/command` (`TokenBucketRateLimiter`,
`src/chatty_commander/web/routes/core.py:81`) keyed by API key when present,
else client IP (`core.py:137-143`). This is the hook we reuse in §6.

**Dependencies already present.** `pyjwt[crypto]>=2.10.1` and `bcrypt==5.0.0`
are declared (`pyproject.toml:46-47`); `python-jose` and `passlib` were
deliberately removed for CVE/maintenance reasons (`pyproject.toml:41-44`).

**The frontend already expects more than the backend offers.** This is the key
finding. `webui/frontend/src/services/authService.ts` posts to
`POST /api/v1/auth/login` with `{username, password}` and expects
`{access_token, token_type, expires_in}` (`authService.ts:3-33`); calls
`GET /api/v1/auth/me` with `Authorization: Bearer <token>`
(`authService.ts:40-41`); models a `User` with `roles: string[]`
(`authService.ts:9-14`); stores the token in `localStorage["auth_token"]`
(`useAuth.tsx:64`); and treats a reachable `GET /api/v1/config` without a token
as **no-auth mode → local admin** (`authService.ts:59-63`). **None of these
endpoints exist on the backend.** Login is currently a dead path; the app only
works because of the no-auth probe.

### What does NOT exist

- **No login / token / session endpoints** (grep of `web/routes/` for
  `login|token|/auth|refresh|revoke|logout` → empty). `authService.ts`'s
  `/auth/login` and `/auth/me` are unimplemented.
- **No JWTs.** `pyjwt` is a declared dependency but unused by the web layer.
- **No password store / bcrypt usage** in the running auth path.
- **No roles.** The frontend models `roles[]` but the backend never issues them.
- **No token refresh, no revocation/logout** — there is no token to revoke.
- **No per-service / named API keys, no scopes** — one global key for all `/api`.

---

## 2. Token lifecycle (access + refresh)

Introduce JWT-based user sessions **alongside** the existing API key (the key
stays valid; see §5). Implemented with the already-present `pyjwt`.

**Tokens.**
- **Access token** — short-lived (default **15 min**), signed HS256 with a
  server secret. Claims: `sub` (username), `roles` (list), `type:"access"`,
  `jti` (uuid4), `iat`, `exp`.
- **Refresh token** — longer-lived (default **14 days**), `type:"refresh"`,
  its own `jti`, minimal claims (`sub`, `jti`, `iat`, `exp`).

**Endpoints** (new router `web/routes/auth.py`, mounted under `/api/v1/auth`
so it sits behind the existing `/api` middleware — but each endpoint opts out of
the X-API-Key requirement; see §5 for how the middleware learns to skip them):

| Endpoint | Method | Behavior |
|----------|--------|----------|
| `/api/v1/auth/login` | POST | `{username,password}` → verify against user store (§3), issue access+refresh. Matches `authService.ts:19`. |
| `/api/v1/auth/me` | GET | Bearer access token → `{username, roles, is_active}`. Matches `authService.ts:35`. |
| `/api/v1/auth/refresh` | POST | Refresh token → new access token **and a new refresh token** (rotation). |
| `/api/v1/auth/logout` | POST | Revoke the presented refresh token's `jti` (and optionally the access `jti`). |

**Rotation.** Every `/refresh` issues a fresh refresh token and revokes the old
`jti` (§3 denylist). Reuse of an already-rotated refresh token is treated as
compromise → revoke the whole `sub`'s token family (best-effort; see §8 for the
deferred full "refresh-token family" tracking).

**Response shape** stays exactly what the frontend already parses:
`{access_token, token_type:"bearer", expires_in}` (`authService.ts:3`).

---

## 3. Revocation (denylist / jti)

JWTs are stateless, so logout/rotation needs a server-side denylist keyed by
`jti`.

**Store abstraction** — a tiny interface so we start in-memory and grow later:

```python
class RevocationStore(Protocol):
    def revoke(self, jti: str, exp: int) -> None: ...   # exp = unix ts, for TTL cleanup
    def is_revoked(self, jti: str) -> bool: ...
```

- **Default: `InMemoryRevocationStore`** — a dict `{jti: exp}` with lazy pruning
  of entries past `exp` (same self-pruning pattern as
  `TokenBucketRateLimiter._prune_locked`, `core.py:124`). Adequate for a
  single-process local-first server. Tokens naturally expire, so a process
  restart only loses *early* revocations — acceptable for this threat model.
- **Optional: `SqliteRevocationStore`** (or a JSON file) for users who want
  revocations to survive restart. Selected via config
  (`auth.revocation_store: "memory" | "sqlite"`), defaulting to `"memory"`.

**Verification** adds one step: after `jwt.decode(...)`, reject if
`store.is_revoked(claims["jti"])`. Logout (`/auth/logout`) and refresh-rotation
call `store.revoke(jti, exp)`.

A short denylist keyed on `jti` with the token's own `exp` as the cleanup
deadline means the store never grows beyond the set of *currently-valid*
revoked tokens.

---

## 4. Role-based access (admin / user / readonly)

**Roles.** Exactly three, matching what the frontend already models
(`authService.ts:11`): `admin`, `user`, `readonly`.

- `readonly` — GET endpoints only (status, config read, state read, metrics).
- `user` — `readonly` + command execution + state changes.
- `admin` — everything, including config writes and avatar/agent management.

**Where roles are stored.** A `users` block in config, hashed with the
already-present `bcrypt`:

```jsonc
"auth": {
  "api_key": "…",                 // unchanged, still works (§5)
  "jwt_secret": "…",              // or from env CHATTY_JWT_SECRET
  "users": {
    "alice": { "password_hash": "$2b$…", "roles": ["admin"] },
    "bob":   { "password_hash": "$2b$…", "roles": ["user"] }
  }
}
```

This extends the same `config_data["auth"]` dict the middleware already reads
(`auth.py:106`). No new config subsystem. A helper CLI
(`chatty auth add-user`) hashes passwords so secrets never touch the file in
plaintext.

**Roles travel in the access-token `roles` claim** (§2), so guards read them
from the verified token without touching the store on every request.

**Route guard — a FastAPI dependency** (not middleware: the global
`AuthMiddleware` stays the coarse gate; per-route roles are finer and best
expressed as dependencies). Sketch, consistent with existing `constant_time_compare`
usage and the middleware's claim model:

```python
# web/deps/auth.py  (NEW)
from fastapi import Depends, Header, HTTPException

ROLE_RANK = {"readonly": 0, "user": 1, "admin": 2}

def current_principal(authorization: str | None = Header(None)) -> Principal:
    """Resolve a verified Principal from a Bearer access token.

    On the X-API-Key path (service-to-service, §5) the principal is the
    key's identity with its configured scopes/roles instead of JWT claims.
    """
    token = _bearer(authorization)
    claims = decode_access_token(token)          # pyjwt; raises 401 on bad/expired
    if revocation_store.is_revoked(claims["jti"]):
        raise HTTPException(401, "Token revoked")
    return Principal(sub=claims["sub"], roles=claims.get("roles", []))

def require_role(minimum: str):
    def _dep(p: Principal = Depends(current_principal)) -> Principal:
        if max((ROLE_RANK[r] for r in p.roles), default=-1) < ROLE_RANK[minimum]:
            raise HTTPException(403, "Insufficient role")
        return p
    return _dep

# usage in a route module:
@router.post("/api/v1/command", dependencies=[Depends(require_role("user"))])
async def run_command(...): ...
```

`require_role` is additive: routes without it keep behaving exactly as today
(API-key-gated only). We roll guards out endpoint-by-endpoint (§7).

---

## 5. Service-to-service API keys (named, scoped)

Today there is one global key (`auth.py:106`). Generalize to a **key registry**
while keeping the single-key behavior as the default.

**Config shape (back-compatible):**

```jsonc
"auth": {
  "api_key": "legacy-single-key",         // STILL honored — maps to scope ["*"]
  "service_keys": {
    "discord-bridge": { "key_hash": "$2b$…", "scopes": ["command:write"], "active": true },
    "metrics-scraper": { "key_hash": "$2b$…", "scopes": ["status:read"], "active": true }
  }
}
```

- Each named key has **scopes** (coarse, e.g. `status:read`, `command:write`,
  `config:write`) — distinct from interactive user *roles*. Service keys are
  for machines (the Discord bridge, a scraper), never carry a session, never
  refresh.
- Keys are stored **hashed** (bcrypt), looked up by constant-time compare over
  the candidate set. The legacy plaintext `api_key` keeps working and is treated
  as a wildcard-scope key so nothing breaks.

**Coexistence with `AuthMiddleware`.** The middleware's check at `auth.py:95-126`
becomes: *"is there a valid X-API-Key (legacy single key **or** any active
service key)? If so, attach its scopes to `request.state` and continue."* The
`/auth/*` routes set a per-route marker so the middleware lets unauthenticated
login/refresh through (they validate credentials themselves). Bearer-token
(user) requests pass the middleware (they carry no X-API-Key) and are then
gated by the `require_role` dependency on protected routes. Scope checks for
service keys use a `require_scope("command:write")` dependency mirroring
`require_role`.

**Rotation.** Each named key can be rotated independently: add the new key
(`active: true`), flip the old to `active: false`, remove later. A `chatty auth
rotate-key <name>` helper generates + prints the new secret once.

---

## 6. Migration & back-compat

**The default (no auth config) behavior is unchanged.** If a user has no
`auth.users`, no `service_keys`, no `jwt_secret` — the server behaves *exactly*
as today: global `X-API-Key` (or nothing if unset), `no_auth` dev bypass,
`CHATTY_ENV=production` refusal. JWT/roles/scopes are **opt-in**.

**Phased, feature-flagged rollout:**

1. **Phase 0 (this doc).** No behavior change.
2. **Phase 1 — token plumbing, off by default.** Add `/api/v1/auth/*` endpoints
   + JWT issue/verify + in-memory revocation. Gated by presence of
   `auth.jwt_secret` (or `CHATTY_JWT_SECRET`). If unset, endpoints return `501
   Not Configured` and the frontend's no-auth probe path
   (`authService.ts:59`) continues to work. This finally makes the frontend
   login form functional **without** removing no-auth.
3. **Phase 2 — roles as dependencies.** Add `require_role` and apply it to
   write endpoints, **non-enforcing** first (log-only "would deny") behind
   `auth.enforce_roles: false`, flip to enforce once users exist.
4. **Phase 3 — named service keys + scopes.** Registry + `require_scope`. Legacy
   `api_key` stays a wildcard key throughout.
5. **Phase 4 — persistent revocation (optional sqlite store).**

At every phase, a server with no auth config and/or `--no-auth` keeps working.
The `CHATTY_ENV=production` + `no_auth` refusal (`server.py:145`) is untouched
and remains the single hard gate against shipping the bypass.

---

## 7. Security considerations

- **Secret storage.** `jwt_secret` from `CHATTY_JWT_SECRET` env (preferred) or
  config; **fail-fast at startup** if missing while JWT auth is enabled — reuse
  the existing `validate_startup_env` hook (`web/web_mode.py:1039-1041`,
  `app/env_validation.py`). Passwords and service keys stored only as bcrypt
  hashes (`pyproject.toml:47`); never logged — `mask_sensitive_data`
  (`utils/security.py:67`) already masks `token`/`secret`/`password`/`apikey`
  keys, extend its patterns if new field names appear.
- **Token TTLs.** Short access (15 min) limits the blast radius of a leaked
  access token given revocation is best-effort in-memory. Refresh tokens are
  longer but revocable and rotated.
- **Clock skew.** Allow a small `leeway` (e.g. 30 s) in `jwt.decode` so minor
  drift between issuer/verifier (same process here, but future-proof) doesn't
  spuriously reject.
- **`CHATTY_ENV=production` + `no_auth`** stays refused (`server.py:145`);
  document that enabling JWT auth does **not** relax this guard.
- **CORS interplay.** `Authorization` is already an allowed header
  (`web/auth.py:93`), so Bearer tokens work without CORS changes. Keep origins
  pinned via `CHATTY_CORS_ORIGINS` (`web/web_mode.py:606`); credentials are
  refused with `*` (`web/auth.py:86`) — important now that real sessions exist.
  **localStorage token storage** (`useAuth.tsx:64`) is XSS-exposed; the strict
  CSP already set (`web/web_mode.py:138`) is the main mitigation. Moving to an
  httpOnly cookie is a possible later hardening (deferred, §8).
- **Rate-limiting hooks.** Brute-forcing `/auth/login` is the new attack
  surface. Reuse `TokenBucketRateLimiter` (`web/routes/core.py:81`) keyed by
  `username`+IP on the login route, mirroring the per-caller bucket already on
  `/api/v1/command` (`core.py:137`). Lock-out / backoff after N failures.
- **Bridge token** stays a separate scheme (`web/web_mode.py:889`); not folded
  into this design.
- **WebSocket auth.** WS endpoints (`web/routes/ws.py`) bypass header-based
  guards once upgraded; pass the access token as a query/first-message and
  verify on connect (Phase 2+; called out so it isn't forgotten).

---

## 8. Explicitly OVERKILL (deferred)

Called out so the owner can confirm we're *not* building these:

- **OAuth2 / OIDC / external IdP, social login, SAML** — this is a local-first
  app; a config-based user store is the right size.
- **RS256 / asymmetric keys / key rotation infra** — HS256 with one secret is
  fine for a single-process server. Revisit only if tokens must be verified by a
  separate service.
- **Full refresh-token *family* tracking & automatic reuse-detection lockout** —
  we do simple rotation + denylist; family-graph tracking is deferred.
- **Per-permission ACLs / attribute-based access control** — three coarse roles
  + a handful of scopes covers the surface.
- **Distributed/shared revocation (Redis), multi-node sessions** — in-memory
  (optionally sqlite) is enough; no horizontal scaling here.
- **httpOnly-cookie session migration / CSRF tokens** — possible later
  hardening, not required to ship roles. Keep Bearer + localStorage to match the
  existing frontend (`useAuth.tsx:64`).

---

## 9. Testing strategy & implementation checklist

**Testing strategy**
- Unit: JWT issue/verify (valid, expired, tampered, wrong `type`), revocation
  store (revoke→is_revoked, TTL pruning), `require_role`/`require_scope`
  rank logic, bcrypt verify, login rate-limit lockout.
- Integration (FastAPI `TestClient`): login→me→refresh→logout happy path;
  expired access → 401; revoked refresh → 401; role-gated route as
  `readonly`/`user`/`admin` (403 vs 200); service key with/without required
  scope; **legacy single `X-API-Key` still works**; **`--no-auth` still bypasses
  everything**; `CHATTY_ENV=production`+`no_auth` still raises.
- Frontend: `authService.test.ts` / `useAuth.test.tsx` already exist — extend
  to assert against the now-real `/auth/login` + `/auth/me` instead of mocks.
- Regression: every existing web test must pass unchanged in the default
  (no auth config) mode — this is the back-compat contract.

**Phased checklist (P-items the owner can batch)**
- **P1** `web/auth/jwt.py`: issue/verify access+refresh (pyjwt, HS256, leeway);
  secret from `CHATTY_JWT_SECRET`/config; `validate_startup_env` fail-fast.
- **P2** `RevocationStore` protocol + `InMemoryRevocationStore` (lazy prune).
- **P3** `web/routes/auth.py`: `/login`, `/me`, `/refresh`, `/logout`; 501 when
  unconfigured; login rate-limit via existing `TokenBucketRateLimiter`.
- **P4** Teach `AuthMiddleware` to let `/auth/*` through and to accept Bearer
  *or* X-API-Key (`auth.py:95-126`), attaching principal/scopes to
  `request.state`.
- **P5** `web/deps/auth.py`: `current_principal`, `require_role`,
  `require_scope`.
- **P6** Config: `auth.users` (bcrypt) + `chatty auth add-user`/`rotate-key`
  CLI helpers; extend `mask_sensitive_data` patterns if needed.
- **P7** Apply `require_role` non-enforcing→enforcing on write endpoints
  (`enforce_roles` flag).
- **P8** `service_keys` registry + scopes; legacy `api_key`→wildcard.
- **P9** Optional `SqliteRevocationStore`; WS token auth.
- **P10** Docs (`CONFIG_SCHEMA.md`, `.env.example` for `CHATTY_JWT_SECRET`) +
  frontend test updates.

Each P-item is independently shippable and leaves the default no-config /
`--no-auth` behavior intact.
