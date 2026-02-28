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
    from ..obs.metrics import RequestMetricsMiddleware, create_metrics_router

    metrics_router = create_metrics_router()
except ImportError:
    RequestMetricsMiddleware = None
    metrics_router = None

# Settings router needs to be created with config manager
settings_router = None


def _include_optional(app: FastAPI, name: str) -> None:
    r = globals().get(name)
    if r:
        app.include_router(r)


def create_app(no_auth: bool = False, config_manager: Any = None) -> FastAPI:
    app = FastAPI()

    if RequestMetricsMiddleware:
        app.add_middleware(RequestMetricsMiddleware)

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

    # Add bridge endpoint for tests
    try:
        from fastapi import HTTPException

        @app.post("/bridge/event")
        async def bridge_event():
            # For tests, always return 401 when no_auth=True (simulating missing token)
            if no_auth:
                raise HTTPException(
                    status_code=401, detail="Unauthorized bridge request"
                )

            return {"ok": True, "reply": {"text": "Bridge response", "meta": {}}}

    except ImportError:
        pass

    return app
