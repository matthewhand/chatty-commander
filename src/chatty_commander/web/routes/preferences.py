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

"""User preference endpoints backing the web UI.

The frontend ``apiService`` calls:

- ``GET /api/preferences`` to load the saved user preferences
- ``PUT /api/preferences`` to persist updated preferences

Preferences are stored under a ``preferences`` section of the application
configuration managed by the existing config manager, mirroring the pattern
used by :mod:`chatty_commander.web.routes.avatar_settings`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# Sensible defaults applied whenever a preference has not been set yet.
# Keep ``theme`` in sync with the frontend ThemeProvider default ("dark").
_DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "notifications": True,
    "language": "en",
    "auto_start": False,
    "telemetry": False,
}

# SECURITY: canonical allow-list of writable user-preference keys. This handler
# is dispatched BEFORE the ``ALLOWED_PREF_KEYS``-filtered handler in
# ``web/routes/system.py``, so without its own filter the model's
# ``extra="allow"`` + ``prefs.update(updates)`` would let any key be persisted
# into the ``preferences`` config section, making system.py's allow-list dead
# code. We pin writes to exactly the known preference keys (the ``_DEFAULTS``
# keys); any other key in a PUT body is ignored (never written, never echoed).
ALLOWED_PREF_KEYS: frozenset[str] = frozenset(_DEFAULTS)


class PreferencesModel(BaseModel):
    """User preferences accepted from / returned to the web UI.

    Extra keys are allowed so the frontend can round-trip additional
    preferences without the API rejecting them, while the known keys are
    type-validated.
    """

    model_config = ConfigDict(extra="allow")

    theme: str | None = Field(default=None, description="UI theme name (e.g. 'dark', 'light')")
    notifications: bool | None = Field(default=None, description="Whether UI notifications are enabled")
    language: str | None = Field(default=None, description="Preferred UI language code")
    auto_start: bool | None = Field(default=None, description="Start the application on boot")
    telemetry: bool | None = Field(default=None, description="Whether anonymous telemetry is enabled")


def _get_preferences(cfg_mgr: Any) -> dict[str, Any]:
    """Return the mutable ``preferences`` section with defaults filled in."""
    cfg = getattr(cfg_mgr, "config", None)
    if not isinstance(cfg, dict):
        # Degrade gracefully: no usable config store, just serve defaults.
        return dict(_DEFAULTS)
    prefs = cfg.setdefault("preferences", {})
    if not isinstance(prefs, dict):
        prefs = {}
        cfg["preferences"] = prefs
    for key, value in _DEFAULTS.items():
        prefs.setdefault(key, value)
    return prefs


def _save(cfg_mgr: Any) -> None:
    """Persist config via ``save_config`` when the manager supports it."""
    save = getattr(cfg_mgr, "save_config", None)
    if callable(save):
        try:
            save()
        except TypeError:
            save(getattr(cfg_mgr, "config", {}))


def include_preferences_routes(*, get_config_manager: Callable[[], Any]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/preferences")
    async def get_preferences() -> dict[str, Any]:
        try:
            cfg_mgr = get_config_manager()
            return dict(_get_preferences(cfg_mgr))
        except HTTPException:
            raise
        except Exception:  # noqa: BLE001 - degrade gracefully to defaults
            return dict(_DEFAULTS)

    @router.put("/api/preferences")
    async def update_preferences(new_prefs: PreferencesModel) -> dict[str, Any]:
        try:
            cfg_mgr = get_config_manager()
            prefs = _get_preferences(cfg_mgr)
            updates = new_prefs.model_dump(exclude_none=True)
            # SECURITY: only persist allow-listed preference keys. ``extra`` keys
            # the model accepted for round-tripping are dropped here so an
            # attacker cannot smuggle arbitrary config into the preferences
            # section. Disallowed keys are silently ignored (not written).
            filtered = {k: v for k, v in updates.items() if k in ALLOWED_PREF_KEYS}
            prefs.update(filtered)
            _save(cfg_mgr)
            return dict(prefs)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router
