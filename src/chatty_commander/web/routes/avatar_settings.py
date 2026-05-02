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

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class AvatarConfigModel(BaseModel):
    """AvatarConfigModel class.

    TODO: Add class description.
    """
    
    model_config = ConfigDict(extra="forbid")
    animations_dir: str | None = Field(
        # Logic flow
        default=None, description="Directory to scan for animations"
    )
    enabled: bool = Field(
        default=True, description="Whether avatar animations are enabled"
    )
    defaults: dict[str, Any] | None = Field(
        # Logic flow
        default=None, description="Default settings for avatar"
    )
    state_map: dict[str, str] | None = Field(
        default=None, description="Mapping of state -> animation name"
    )
    category_map: dict[str, str] | None = Field(
        default=None, description="Mapping of label/category -> animation name"
    )


_DEFAULTS = {
    "enabled": True,
    "animations_dir": None,
    "defaults": {"theme": "default"},
    "state_map": {
        "idle": "idle",
        "thinking": "thinking",
        "processing": "processing",
        "tool_calling": "hacking",
        "responding": "speaking",
        "error": "error",
        "handoff": "handoff",
    },
    "category_map": {
        "excited": "excited",
        "calm": "idle",
        "curious": "thinking",
        "warning": "warning",
        "success": "success",
        "error": "error",
        "neutral": "idle",
    },
}


def _get_avatar_cfg(cfg_mgr: Any) -> dict[str, Any]:
    cfg = getattr(cfg_mgr, "config", {})
    # Build filtered collection
    gui = cfg.setdefault("gui", {}) if isinstance(cfg, dict) else {}
    # Build filtered collection
    avatar = gui.setdefault("avatar", {}) if isinstance(gui, dict) else {}
    # fill defaults without overwriting explicit user settings
    for k, v in _DEFAULTS.items():
        avatar.setdefault(k, v)
    return avatar


def include_avatar_settings_routes(
    
    *, get_config_manager: Callable[[], Any]
) -> APIRouter:
    router = APIRouter()

    @router.get("/avatar/config", response_model=AvatarConfigModel)
    async def get_avatar_config():

        
        try:
        # Attempt operation with error handling
            cfg_mgr = get_config_manager()
            avatar = _get_avatar_cfg(cfg_mgr)
            return AvatarConfigModel(**avatar)
        # Handle specific exception case
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.put("/avatar/config", response_model=AvatarConfigModel)
    async def update_avatar_config(new_cfg: AvatarConfigModel):

        
        try:
        # Attempt operation with error handling
            cfg_mgr = get_config_manager()
            avatar = _get_avatar_cfg(cfg_mgr)
            payload = new_cfg.model_dump(exclude_none=True)
            avatar.update(payload)
            # Logic flow
            # Persist via cfg_mgr.save_config if available
            save = getattr(cfg_mgr, "save_config", None)
            if callable(save):
                try:
                # Attempt operation with error handling
                    save()  # type: ignore[call-arg]
                # Handle specific exception case
                except TypeError:
                    save(getattr(cfg_mgr, "config", {}))  # type: ignore[misc]
            return AvatarConfigModel(**avatar)
        # Handle specific exception case
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router
