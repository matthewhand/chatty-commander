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

from __future__ import annotations

import logging
import os
from typing import Any

from chatty_commander.utils.security import constant_time_compare

try:
    from fastapi import FastAPI
except Exception:  # very minimal stub if FastAPI missing (tests won't hit real HTTP)

    class FastAPI:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None: ...

        def include_router(self, *a: Any, **k: Any) -> None: ...

        @property
        def routes(self):
            return []


# Import all available routers
try:
    from .routes.avatar_ws import router as avatar_ws_router
except ImportError:
    avatar_ws_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_api import router as avatar_api_router
except ImportError:
    avatar_api_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_selector import router as avatar_selector_router
except ImportError:
    avatar_selector_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_settings import include_avatar_settings_routes
except ImportError:
    include_avatar_settings_routes = None  # type: ignore[assignment]

try:
    from .routes.audio import include_audio_routes
except ImportError:
    include_audio_routes = None  # type: ignore[assignment]

try:
    from .routes.preferences import include_preferences_routes
except ImportError:
    include_preferences_routes = None  # type: ignore[assignment]

try:
    from .routes.themes import include_theme_routes
except ImportError:
    include_theme_routes = None  # type: ignore[assignment]

try:
    from .routes.version import router as version_router
except ImportError:
    version_router = None  # type: ignore[assignment]

try:
    from .routes.voice_test import register_voice_test_routes
except ImportError:
    register_voice_test_routes = None  # type: ignore[assignment]

try:
    from .routes.auth import register_auth_routes
except ImportError:
    register_auth_routes = None  # type: ignore[assignment]

try:
    from .routes.dograh import router as dograh_router
except ImportError:
    dograh_router = None  # type: ignore[assignment]

try:
    from .routes.agents import router as agents_router
except ImportError:
    agents_router = None  # type: ignore[assignment]

try:
    from .routes.models import router as models_router
except ImportError:
    models_router = None  # type: ignore[assignment]

try:
    from .routes.system import include_system_routes

except ImportError:
    include_system_routes = None  # type: ignore[assignment]

try:
    from .routes.command_authoring import router as command_authoring_router
except ImportError:
    command_authoring_router = None  # type: ignore[assignment]

try:
    from ..obs.metrics import create_metrics_router

    metrics_router = create_metrics_router()
except ImportError:
    metrics_router = None  # type: ignore[assignment]

# Settings router needs to be created with config manager
settings_router = None


def _include_optional(app: FastAPI, name: str) -> None:
    """Include optional router from globals if present."""
    r = globals().get(name)
    if r:
        app.include_router(r)


def ensure_no_auth_allowed(no_auth: bool) -> None:
    """Refuse the development auth bypass in production environments.

    ``no_auth=True`` disables authentication entirely and exists purely as a
    development convenience. To prevent it ever reaching production, this
    guard raises ``RuntimeError`` at app-factory time when the deployment
    environment is marked as production.

    The canonical environment indicator is the ``CHATTY_ENV`` environment
    variable (chosen deliberately over generic alternatives such as
    ``ENVIRONMENT`` or ``NODE_ENV`` so there is exactly one switch to set and
    audit). The check is case-insensitive: ``CHATTY_ENV=production`` (or
    ``Production`` etc.) combined with ``no_auth=True`` is refused.

    Called by both FastAPI app factories — ``server.create_app`` and
    ``web_mode.WebModeServer._create_app`` — so neither path can drift.
    """
    if no_auth and os.environ.get("CHATTY_ENV", "").strip().lower() == "production":
        raise RuntimeError(
            "no_auth=True is a development bypass and refuses to run with "
            "CHATTY_ENV=production"
        )


def register_shared_routers(
    app: FastAPI, config_manager: Any = None, *, no_auth: bool = False
) -> None:
    """Register routers shared by both FastAPI app factories.

    Single source of truth for the router set used by both
    ``server.create_app`` and ``web_mode.WebModeServer._create_app``.
    Add new shared routers here instead of duplicating the list in each
    factory.

    Covers the import-guarded routers (avatar ws/api/selector, version,
    dograh, metrics, agents) plus the config-bound factories (audio,
    preferences, themes).

    ``no_auth`` is threaded through so the Phase-2 role dependency
    (``web/deps/auth.py``) can apply its degradation rule: role guards are a
    pass-through (allow) unless user auth is active (users configured AND not
    ``no_auth`` AND a JWT secret is resolvable). It defaults to ``False`` so
    existing callers/tests are unaffected.
    """
    for nm in (
        "avatar_ws_router",
        "avatar_api_router",
        "avatar_selector_router",
        "version_router",
        "dograh_router",
        "metrics_router",
        "agents_router",
    ):
        _include_optional(app, nm)

    if include_audio_routes is not None and config_manager:
        app.include_router(
            include_audio_routes(get_config_manager=lambda: config_manager)
        )

    if include_preferences_routes is not None:
        app.include_router(
            include_preferences_routes(get_config_manager=lambda: config_manager)
        )

    if include_theme_routes is not None:
        app.include_router(
            include_theme_routes(get_config_manager=lambda: config_manager)
        )

    if register_voice_test_routes is not None:
        register_voice_test_routes(app, config_manager)

    # JWT user-login router (/api/v1/auth/*). Self-disables (404) unless
    # auth.users is configured, so default/no-auth flows are unchanged.
    #
    # Share ONE revocation store between the /auth/* router (which writes it on
    # logout/refresh) and the Phase-2 role dependency (which reads it on every
    # guarded request), then publish {config_manager, no_auth, store} on the
    # process-wide AuthContext so require_role can see them. The context is
    # always configured (even when the auth router import is unavailable) so
    # the degradation rule resolves consistently.
    shared_revocation_store = None
    try:
        from .revocation import InMemoryRevocationStore

        shared_revocation_store = InMemoryRevocationStore()
    except ImportError:
        pass

    if register_auth_routes is not None:
        register_auth_routes(
            app, config_manager, revocation_store=shared_revocation_store
        )

    try:
        from .deps.auth import configure_auth_context

        configure_auth_context(
            config_manager=config_manager,
            no_auth=no_auth,
            revocation_store=shared_revocation_store,
        )
    except ImportError:
        pass

    # Standardized {error, code, details, request_id} bodies on /api/* paths
    # for HTTPException, 422 validation and unhandled exceptions. Registered
    # here so both app factories get identical error behavior. No-ops on the
    # minimal FastAPI stub; idempotent across repeat calls.
    try:
        from .errors import register_error_handlers

        register_error_handlers(app)
    except ImportError:
        pass


def create_app(no_auth: bool = False, config_manager: Any = None) -> FastAPI:
    # Structural production refusal: never allow the dev auth bypass when
    # CHATTY_ENV=production (see ensure_no_auth_allowed for the rationale).
    ensure_no_auth_allowed(no_auth)

    app = FastAPI()

    # Auth middleware (protects /api routes globally); mirrors the wiring in
    # web_mode.WebModeServer._create_app so servers built via create_app are
    # not left unauthenticated when no_auth is False.
    if hasattr(app, "add_middleware"):
        try:
            from chatty_commander.web.middleware.auth import AuthMiddleware

            app.add_middleware(
                AuthMiddleware, config_manager=config_manager, no_auth=no_auth
            )
        except ImportError:
            logging.getLogger(__name__).warning(
                "AuthMiddleware unavailable; /api routes are unprotected"
            )

        # Request-ID middleware (added last so it is outermost): echoes or
        # generates X-Request-ID and exposes it to log records via contextvar.
        # web_mode.WebModeServer._create_app wires this separately; it cannot
        # live in register_shared_routers without double-adding it there.
        try:
            from chatty_commander.web.middleware.request_id import RequestIdMiddleware

            if RequestIdMiddleware is not None:
                app.add_middleware(RequestIdMiddleware)
        except ImportError:
            pass

    # Routers shared with web_mode.WebModeServer._create_app (single source
    # of truth lives in register_shared_routers above).
    register_shared_routers(app, config_manager, no_auth=no_auth)

    # Routers exposed only via this factory
    for nm in ("models_router", "command_authoring_router"):
        _include_optional(app, nm)

    # Handle settings router separately since it needs config manager
    if include_avatar_settings_routes is not None and config_manager:
        global settings_router
        settings_router = include_avatar_settings_routes(
            get_config_manager=lambda: config_manager
        )
        _include_optional(app, "settings_router")

    # Add bridge endpoint for tests
    try:
        from fastapi import Header, HTTPException

        # Logger for security events on bridge endpoint
        _bridge_logger = logging.getLogger("chatty_commander.bridge")

        @app.post("/bridge/event")
        async def bridge_event(
            x_bridge_token: str | None = Header(None, alias="X-Bridge-Token"),
        ):
            """Bridge event endpoint for external integrations (e.g., Discord).

            Security behavior:
            - no_auth=True (dev mode): Requires X-Bridge-Token header. Requests without
              token are rejected with 401. This ensures even dev environments require
              authentication to prevent accidental exposure.
            - no_auth=False (production): Requires valid bridge_token from config.
              If bridge_token is missing/empty in config, requests are rejected with 401
              and a warning is logged (secure-by-default).
            """
            if no_auth:
                # Dev mode: token required, reject if missing
                if not x_bridge_token:
                    _bridge_logger.warning(
                        "Bridge request rejected: missing X-Bridge-Token in dev mode"
                    )
                    raise HTTPException(
                        status_code=401, detail="Unauthorized bridge request"
                    )
                return {
                    "ok": True,
                    "reply": {"text": "Bridge response (dev)", "meta": {}},
                }
            else:
                # Production mode: validate token from config
                expected_token: str | None = None
                if config_manager and hasattr(config_manager, "web_server"):
                    expected_token = config_manager.web_server.get("bridge_token")

                # Secure-by-default: reject if token not configured
                if not expected_token:
                    _bridge_logger.warning(
                        "Bridge request rejected: bridge_token not configured in web_server settings"
                    )
                    raise HTTPException(
                        status_code=401,
                        detail="Bridge authentication not configured. Contact administrator.",
                    )

                # Validate token
                if not constant_time_compare(x_bridge_token, expected_token):
                    _bridge_logger.warning(
                        "Bridge request rejected: invalid token provided"
                    )
                    raise HTTPException(status_code=401, detail="Invalid bridge token")

                return {"ok": True, "reply": {"text": "Bridge response", "meta": {}}}


    except ImportError:
        pass

    return app
