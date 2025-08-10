from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


class AvatarConfigModel(BaseModel):
    animations_dir: str | None = Field(default=None, description="Directory to scan for animations")
    enabled: bool = Field(default=True, description="Whether avatar animations are enabled")
    defaults: dict[str, Any] | None = Field(default=None, description="Default settings for avatar")
    state_map: dict[str, str] | None = Field(default=None, description="Mapping of state -> animation name")
    category_map: dict[str, str] | None = Field(default=None, description="Mapping of label/category -> animation name")


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
    gui = cfg.setdefault("gui", {}) if isinstance(cfg, dict) else {}
    avatar = gui.setdefault("avatar", {}) if isinstance(gui, dict) else {}
    # fill defaults without overwriting explicit user settings
    for k, v in _DEFAULTS.items():
        avatar.setdefault(k, v)
    return avatar


def include_avatar_settings_routes(*, get_config_manager: Callable[[], Any]) -> APIRouter:
    router = APIRouter()

    @router.get("/avatar/config", response_model=AvatarConfigModel)
    async def get_avatar_config():
        try:
            cfg_mgr = get_config_manager()
            avatar = _get_avatar_cfg(cfg_mgr)
            return AvatarConfigModel(**avatar)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.put("/avatar/config", response_model=AvatarConfigModel)
    async def update_avatar_config(new_cfg: AvatarConfigModel):
        try:
            cfg_mgr = get_config_manager()
            avatar = _get_avatar_cfg(cfg_mgr)
            payload = new_cfg.model_dump(exclude_none=True)
            avatar.update(payload)
            # Persist via cfg_mgr.save_config if available
            save = getattr(cfg_mgr, "save_config", None)
            if callable(save):
                try:
                    save()  # type: ignore[call-arg]
                except TypeError:
                    save(getattr(cfg_mgr, "config", {}))  # type: ignore[misc]
            return AvatarConfigModel(**avatar)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e)) from e

    return router
