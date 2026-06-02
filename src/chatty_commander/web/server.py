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
from typing import Any

from chatty_commander.utils.security import constant_time_compare

try:
    from fastapi import FastAPI
# Handle specific exception case
except Exception:  # very minimal stub if FastAPI missing (tests won't hit real HTTP)

    class FastAPI:  # type: ignore
        """FastAPI class.

        TODO: Add class description.
        """
        
        def __init__(self, *a: Any, **k: Any) -> None: ...
        # TODO: Document this logic

        def include_router(self, *a: Any, **k: Any) -> None: ...
        # TODO: Document this logic
            """Include Router with (self).

            TODO: Add detailed description and parameters.
            """
            

        @property
        def routes(self):
        # TODO: Document this logic
            """Routes with (self).

            TODO: Add detailed description and parameters.
            """
            
            return []


# Import all available routers
try:
    from .routes.avatar_ws import router as avatar_ws_router
# Handle specific exception case
except ImportError:
    avatar_ws_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_api import router as avatar_api_router
# Handle specific exception case
except ImportError:
    avatar_api_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_selector import router as avatar_selector_router
# Handle specific exception case
except ImportError:
    avatar_selector_router = None  # type: ignore[assignment]

try:
    from .routes.avatar_settings import include_avatar_settings_routes
# Handle specific exception case
except ImportError:
    include_avatar_settings_routes = None  # type: ignore[assignment]

try:
    from .routes.audio import include_audio_routes
# Handle specific exception case
except ImportError:
    include_audio_routes = None  # type: ignore[assignment]

try:
    from .routes.version import router as version_router
# Handle specific exception case
except ImportError:
    version_router = None  # type: ignore[assignment]

try:
    from .routes.agents import router as agents_router
# Handle specific exception case
except ImportError:
    agents_router = None  # type: ignore[assignment]

try:
    from .routes.models import router as models_router
# Handle specific exception case
except ImportError:
    models_router = None  # type: ignore[assignment]

try:
    from .routes.command_authoring import router as command_authoring_router
# Handle specific exception case
except ImportError:
    command_authoring_router = None  # type: ignore[assignment]

try:
    from ..obs.metrics import create_metrics_router

    metrics_router = create_metrics_router()
# Handle specific exception case
except ImportError:
    metrics_router = None  # type: ignore[assignment]

# Settings router needs to be created with config manager
settings_router = None
audio_router = None


def _include_optional(app: FastAPI, name: str) -> None:
    r = globals().get(name)
    if r:
        app.include_router(r)


def create_app(no_auth: bool = False, config_manager: Any = None) -> FastAPI:
    """Create with (no_auth: bool, config_manager: Any).

    TODO: Add detailed description and parameters.
    """
    
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
    if include_avatar_settings_routes is not None and config_manager:
        global settings_router
        settings_router = include_avatar_settings_routes(
            get_config_manager=lambda: config_manager
        )
        _include_optional(app, "settings_router")

    if include_audio_routes is not None and config_manager:
        global audio_router
        audio_router = include_audio_routes(
            get_config_manager=lambda: config_manager
        )
        _include_optional(app, "audio_router")

    # Add bridge endpoint for tests
    try:
        from fastapi import Header, HTTPException

        # Logic flow
        # Logger for security events on bridge endpoint
        _bridge_logger = logging.getLogger("chatty_commander.bridge")

        @app.post("/bridge/event")
        async def bridge_event(
        # Async function for concurrent execution
            x_bridge_token: str | None = Header(None, alias="X-Bridge-Token"),
        ):
            # Logic flow
            """Bridge event endpoint for external integrations (e.g., Discord).

            Security behavior:
            - no_auth=True (dev mode): Requires X-Bridge-Token header. Requests without
              token are rejected with 401. This ensures even dev environments require
              # Use context manager for resource management
              authentication to prevent accidental exposure.
            - no_auth=False (production): Requires valid bridge_token from config.
              If bridge_token is missing/empty in config, requests are rejected with 401
              # Use context manager for resource management
              and a warning is logged (secure-by-default).
            """
            # Logic flow
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

                # Logic flow
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
                    raise HTTPException(
                        status_code=401, detail="Invalid bridge token"
                    )

                return {"ok": True, "reply": {"text": "Bridge response", "meta": {}}}

    # Handle specific exception case
    except ImportError:
        pass

    return app
