from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


class SystemStatus(BaseModel):
    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")


class StateChangeRequest(BaseModel):
    state: str = Field(..., description="Target state", pattern="^(idle|computer|chatty)$")


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(default=None, description="Optional parameters")


class CommandResponse(BaseModel):
    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Execution result message")
    execution_time: float = Field(..., description="Execution time in milliseconds")


class StateInfo(BaseModel):
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of active models")
    last_command: str | None = Field(default=None, description="Last detected command")
    timestamp: str = Field(..., description="Timestamp of last state change")


def include_core_routes(
    *,
    get_start_time: Callable[[], float],
    get_state_manager: Callable[[], Any],
    get_config_manager: Callable[[], Any],
    get_last_command: Callable[[], str | None],
    get_last_state_change: Callable[[], datetime],
    execute_command_fn: Callable[[str], Any],
) -> APIRouter:
    """
    Provide core REST routes as an APIRouter. This module is pure routing; it pulls
    required data/functionality through callables to avoid tight coupling.

    The signatures match what legacy web_mode currently exposes.
    """
    router = APIRouter()

    def _format_uptime(seconds: float) -> str:
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds_i = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds_i}s"
        return f"{hours}h {minutes}m {seconds_i}s"

    @router.get("/api/v1/status", response_model=SystemStatus)
    async def get_status():
        uptime_seconds = time.time() - get_start_time()
        uptime_str = _format_uptime(uptime_seconds)
        sm = get_state_manager()
        return SystemStatus(
            status="running",
            current_state=getattr(sm, "current_state", "idle"),
            active_models=sm.get_active_models() if hasattr(sm, "get_active_models") else [],
            uptime=uptime_str,
        )

    @router.get("/api/v1/config")
    async def get_config():
        cfg_mgr = get_config_manager()
        return getattr(cfg_mgr, "config", {})

    @router.put("/api/v1/config")
    async def update_config(config_data: dict[str, Any]):
        try:
            cfg_mgr = get_config_manager()
            cfg = getattr(cfg_mgr, "config", {})
            if isinstance(cfg, dict):
                cfg.update(config_data)
            save = getattr(cfg_mgr, "save_config", None)
            if callable(save):
                try:
                    save()
                except TypeError:
                    # Some implementations require the cfg param
                    save(cfg)  # type: ignore[arg-type]
            return {"message": "Configuration updated successfully"}
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err)) from err

    @router.get("/api/v1/state", response_model=StateInfo)
    async def get_state():
        sm = get_state_manager()
        return StateInfo(
            current_state=getattr(sm, "current_state", "idle"),
            active_models=sm.get_active_models() if hasattr(sm, "get_active_models") else [],
            last_command=get_last_command(),
            timestamp=get_last_state_change().isoformat(),
        )

    @router.post("/api/v1/state")
    async def change_state(request: StateChangeRequest):
        try:
            sm = get_state_manager()
            sm.change_state(request.state)
            # Legacy broadcast occurs elsewhere; preserve behavior here as data-only change.
            return {"message": f"State changed to {request.state}"}
        except Exception as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

    @router.post("/api/v1/command", response_model=CommandResponse)
    async def execute_command(request: CommandRequest):
        start_time = time.time()
        try:
            cfg_mgr = get_config_manager()
            config_dict = getattr(cfg_mgr, "config", {})
            model_actions = (
                config_dict.get("model_actions", {}) if isinstance(config_dict, dict) else {}
            )
            if request.command not in model_actions:
                raise HTTPException(
                    status_code=404, detail=f"Command '{request.command}' not found"
                )

            # Delegate to provided executor bridge to ensure consistent integration surface
            success = bool(execute_command_fn(request.command))
            execution_time = (time.time() - start_time) * 1000
            return CommandResponse(
                success=success,
                message=(
                    "Command executed successfully" if success else "Command execution failed"
                ),
                execution_time=execution_time,
            )
        except HTTPException:
            raise
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return CommandResponse(
                success=False,
                message=f"Command execution failed: {str(e)}",
                execution_time=execution_time,
            )

    @router.get("/api/v1/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": _format_uptime(time.time() - get_start_time()),
        }

    return router
