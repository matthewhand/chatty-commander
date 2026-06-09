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

"""UI theme endpoints.

The frontend (DaisyUI based) renders themes purely client side via the
``data-theme`` attribute; the backend just needs to list the supported theme
names and persist the user's selection in the config under ``ui.theme`` so
that ``GET /api/v1/config`` returns it on the next page load (see
``webui/frontend/src/components/ThemeProvider.tsx``).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Must stay in sync with the DaisyUI theme list in
# webui/frontend/tailwind.config.js and the <select> options in
# webui/frontend/src/pages/ConfigurationPage.tsx
AVAILABLE_THEMES: tuple[str, ...] = ("dark", "light", "cyberpunk", "synthwave")
DEFAULT_THEME = "dark"


class ThemesResponse(BaseModel):
    themes: list[str] = Field(..., description="Available UI theme names")
    current: str = Field(..., description="Currently selected theme")


class ThemeResponse(BaseModel):
    theme: str = Field(..., description="Currently selected theme")


class ThemeRequest(BaseModel):
    theme: str = Field(..., description="Theme name to select")


class ThemeSetResponse(BaseModel):
    success: bool = Field(True, description="Whether the theme was applied")
    theme: str = Field(..., description="The theme that is now active")


def include_theme_routes(
    *,
    get_config_manager: Callable[[], Any],
) -> APIRouter:
    router = APIRouter()

    def _current_theme() -> str:
        try:
            cfg_mgr = get_config_manager()
            cfg = getattr(cfg_mgr, "config", None)
            if isinstance(cfg, dict):
                theme = (cfg.get("ui") or {}).get("theme")
                if isinstance(theme, str) and theme:
                    return theme
        except Exception as exc:  # degrade gracefully — theme is cosmetic
            logger.debug("Could not read theme from config: %s", exc)
        return DEFAULT_THEME

    @router.get("/api/themes", response_model=ThemesResponse)
    async def get_themes() -> ThemesResponse:
        """List the UI themes the frontend can render."""
        return ThemesResponse(themes=list(AVAILABLE_THEMES), current=_current_theme())

    @router.get("/api/theme", response_model=ThemeResponse)
    async def get_theme() -> ThemeResponse:
        """Return the currently selected UI theme."""
        return ThemeResponse(theme=_current_theme())

    @router.post("/api/theme", response_model=ThemeSetResponse)
    async def set_theme(request: ThemeRequest) -> ThemeSetResponse:
        """Select a UI theme and persist it under ``ui.theme`` in the config."""
        theme = (request.theme or "").strip()
        if theme not in AVAILABLE_THEMES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown theme {request.theme!r}. "
                    f"Available themes: {', '.join(AVAILABLE_THEMES)}"
                ),
            )

        # Persist via the config manager when available; the UI applies the
        # theme client-side regardless, so persistence failures are non-fatal.
        try:
            cfg_mgr = get_config_manager()
            cfg = getattr(cfg_mgr, "config", None)
            if isinstance(cfg, dict):
                cfg.setdefault("ui", {})["theme"] = theme
                if hasattr(cfg_mgr, "save_config"):
                    cfg_mgr.save_config()
        except Exception as exc:
            logger.warning("Failed to persist theme %r: %s", theme, exc)

        return ThemeSetResponse(success=True, theme=theme)

    return router
