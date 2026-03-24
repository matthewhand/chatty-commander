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
import secrets
from typing import Any

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
    avatar_ws_router = None

try:
    from .routes.avatar_api import router as avatar_api_router
except ImportError:
    avatar_api_router = None

try:
    from .routes.avatar_selector import router as avatar_selector_router
except ImportError:
    avatar_selector_router = None

try:
    from .routes.avatar_settings import include_avatar_settings_routes
except ImportError:
    include_avatar_settings_routes = None

try:
    from .routes.audio import include_audio_routes
except ImportError:
    include_audio_routes = None

try:
    from .routes.version import router as version_router
except ImportError:
    version_router = None

try:
    from .routes.agents import router as agents_router
except ImportError:
    agents_router = None

try:
    from .routes.models import router as models_router
except ImportError:
    models_router = None

try:
    from .routes.command_authoring import router as command_authoring_router
except ImportError:
    command_authoring_router = None

try:
    from ..obs.metrics import create_metrics_router

    metrics_router = create_metrics_router()
except ImportError:
    metrics_router = None

# Settings router needs to be created with config manager
settings_router = None
audio_router = None


def _include_optional(app: FastAPI, name: str) -> None:
    r = globals().get(name)
    if r:
        app.include_router(r)


def create_app(no_auth: bool = False, config_manager: Any = None) -> FastAPI:
    app = FastAPI()

    # Include routers that are available
    for nm in (
        "avatar_ws_router",
        "avatar_api_router",
        "avatar_selector_router",
        "version_router",
        "metrics_router",
        "agents_router",
        "models_router",
        "command_authoring_router",
    ):
        _include_optional(app, nm)

    # Handle settings router separately since it needs config manager
    if include_avatar_settings_routes and config_manager:
        global settings_router
        settings_router = include_avatar_settings_routes(
            get_config_manager=lambda: config_manager
        )
        _include_optional(app, "settings_router")

    if include_audio_routes and config_manager:
        global audio_router
        audio_router = include_audio_routes(
            get_config_manager=lambda: config_manager
        )
        _include_optional(app, "audio_router")

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
                    _bridge_logger.warning("Bridge request rejected: missing X-Bridge-Token in dev mode")
                    raise HTTPException(
                        status_code=401, detail="Unauthorized bridge request"
                    )
                return {"ok": True, "reply": {"text": "Bridge response (dev)", "meta": {}}}
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
                if not x_bridge_token or not secrets.compare_digest(x_bridge_token.encode("utf-8"), str(expected_token).encode("utf-8")):
                    _bridge_logger.warning(
                        "Bridge request rejected: invalid token provided"
                    )
                    raise HTTPException(
                        status_code=401, detail="Invalid bridge token"
                    )

                return {"ok": True, "reply": {"text": "Bridge response", "meta": {}}}

    except ImportError:
        pass

    return app
