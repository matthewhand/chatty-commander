from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
except Exception:  # very minimal stub if FastAPI missing (tests won’t hit real HTTP)
    class FastAPI:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None: ...
        def include_router(self, *a: Any, **k: Any) -> None: ...
        @property
        def routes(self): return []

def _include_optional(app: FastAPI, name: str) -> None:
    r = globals().get(name)
    if r:
        app.include_router(r)

def create_app(no_auth: bool = False) -> FastAPI:
    app = FastAPI()
    for nm in (
        "avatar_ws_router","avatar_api_router",
        "settings_router","avatar_selector_router",
        "version_router","metrics_router","agents_router"
    ):
        _include_optional(app, nm)
    return app
