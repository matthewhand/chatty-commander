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
    state: str = Field(
        ..., description="Target state", pattern="^(idle|computer|chatty)$"
    )


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(
        default=None, description="Optional parameters"
    )


class CommandResponse(BaseModel):
    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Execution result message")
    execution_time: float = Field(..., description="Execution time in milliseconds")


class StateInfo(BaseModel):
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of active models")
    last_command: str | None = Field(default=None, description="Last detected command")
    timestamp: str = Field(..., description="Timestamp of last state change")


class HealthStatus(BaseModel):
    status: str = Field(..., description="Health status")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")
    database: str = Field(default="unknown", description="Database status")
    memory_usage: str = Field(default="unknown", description="Memory usage")
    cpu_usage: str = Field(default="unknown", description="CPU usage")
    last_health_check: str = Field(..., description="Last health check timestamp")


class MetricsData(BaseModel):
    total_requests: int = Field(..., description="Total API requests")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    active_connections: int = Field(
        default=0, description="Active WebSocket connections"
    )
    cache_size: int = Field(default=0, description="Cache entries count")
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    response_time_avg: float = Field(
        default=0.0, description="Average response time in ms"
    )


def include_core_routes(
    *,
    get_start_time: Callable[[], float],
    get_state_manager: Callable[[], Any],
    get_config_manager: Callable[[], Any],
    get_last_command: Callable[[], str | None],
    get_last_state_change: Callable[[], datetime],
    execute_command_fn: Callable[[str], Any],
    get_active_connections: Callable[[], int] | None = None,
    get_cache_size: Callable[[], int] | None = None,
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
            active_models=sm.get_active_models()
            if hasattr(sm, "get_active_models")
            else [],
            uptime=uptime_str,
        )

    @router.get("/health", response_model=HealthStatus)
    async def health_check():
        """Comprehensive health check endpoint."""
        uptime_seconds = time.time() - get_start_time()
        uptime_str = _format_uptime(uptime_seconds)

        # Basic system checks
        memory_usage = "unknown"
        cpu_usage = "unknown"

        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_usage = ".1f"
            cpu_usage = ".1f"
        except ImportError:
            pass  # psutil not available

        # Database check (placeholder for future database integration)
        database_status = "not_configured"

        return HealthStatus(
            status="healthy",
            uptime=uptime_str,
            version="0.2.0",
            database=database_status,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            last_health_check=datetime.now().isoformat(),
        )

    @router.get("/metrics", response_model=MetricsData)
    async def get_metrics():
        """Get application metrics and performance data."""
        uptime_seconds = time.time() - get_start_time()
        total_requests = sum(counters.values())

        active_connections = 0
        if get_active_connections:
            try:
                active_connections = get_active_connections()
            except Exception:
                pass

        cache_size = 0
        if get_cache_size:
            try:
                cache_size = get_cache_size()
            except Exception:
                pass

        # Calculate error rate (simplified)
        error_count = counters.get("errors", 0)
        error_rate = (error_count / max(total_requests, 1)) * 100

        return MetricsData(
            total_requests=total_requests,
            uptime_seconds=uptime_seconds,
            active_connections=active_connections,
            cache_size=cache_size,
            error_rate=round(error_rate, 2),
            response_time_avg=0.0,  # Placeholder for future implementation
        )

    @router.get("/api/v1/config")
    async def get_config():
        counters["config_get"] += 1
        cfg_mgr = get_config_manager()
        return getattr(cfg_mgr, "config", {})

    @router.put("/api/v1/config")
    async def update_config(config_data: dict[str, Any]):
        counters["config_put"] += 1
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
        counters["state_get"] += 1
        sm = get_state_manager()
        return StateInfo(
            current_state=getattr(sm, "current_state", "idle"),
            active_models=sm.get_active_models()
            if hasattr(sm, "get_active_models")
            else [],
            last_command=get_last_command(),
            timestamp=get_last_state_change().isoformat(),
        )

    @router.post("/api/v1/state")
    async def change_state(request: StateChangeRequest):
        counters["state_post"] += 1
        try:
            sm = get_state_manager()
            sm.change_state(request.state)
            # Legacy broadcast occurs elsewhere; preserve behavior here as data-only change.
            return {"message": f"State changed to {request.state}"}
        except Exception as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

    @router.post("/api/v1/command", response_model=CommandResponse)
    async def execute_command(request: CommandRequest):
        counters["command_post"] += 1
        start_time = time.time()
        try:
            cfg_mgr = get_config_manager()
            config_dict = getattr(cfg_mgr, "config", {})
            model_actions = (
                config_dict.get("model_actions", {})
                if isinstance(config_dict, dict)
                else {}
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
                    "Command executed successfully"
                    if success
                    else "Command execution failed"
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

    # Basic in-memory metrics counters (per-router instance)
    counters = {
        "status": 0,
        "config_get": 0,
        "config_put": 0,
        "state_get": 0,
        "state_post": 0,
        "command_post": 0,
    }

    @router.get("/api/v1/health", operation_id="health_check_core")
    async def health_check():
        counters["status"] += 1
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": _format_uptime(time.time() - get_start_time()),
        }

    @router.get("/api/v1/metrics")
    async def metrics():
        # Shallow copy to avoid external mutation
        return {**counters}

    return router
