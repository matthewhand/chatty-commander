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

import asyncio
import logging
import os
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware

from chatty_commander.utils.security import mask_sensitive_data

logger = logging.getLogger(__name__)

_ENGINES: dict[str, tuple[Any, float]] = {}  # (engine, creation_time)
_ENGINES_LOCK = threading.Lock()
_MAX_ENGINES = 10  # Maximum cached engines to prevent unbounded memory growth
_ENGINE_TTL_SECONDS = 3600  # 1 hour TTL for cached engines
_ENGINE_CACHE_HITS = 0
_ENGINE_CACHE_MISSES = 0

ALLOWED_CONFIG_KEYS = frozenset(
    {
        "general",
        "audio_settings",
        "ui",
        "logging",
        "voice_only",
        "default_state",
        "voice",
    }
)


class SystemStatus(BaseModel):
    """SystemStatus class.

    TODO: Add class description.
    """
    
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")


class StateChangeRequest(BaseModel):
    """StateChangeRequest class.

    TODO: Add class description.
    """
    
    model_config = ConfigDict(extra="forbid")

    state: str = Field(
        ..., description="Target state", pattern="^(idle|computer|chatty)$"
    )


class CommandRequest(BaseModel):
    """CommandRequest class.

    TODO: Add class description.
    """
    
    model_config = ConfigDict(extra="forbid")

    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(
        default=None, description="Optional parameters"
    )


class CommandResponse(BaseModel):
    """CommandResponse class.

    TODO: Add class description.
    """
    
    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Execution result message")
    execution_time: float = Field(..., description="Execution time in milliseconds")


class StateInfo(BaseModel):
    """StateInfo class.

    TODO: Add class description.
    """
    
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of active models")
    last_command: str | None = Field(default=None, description="Last detected command")
    timestamp: str = Field(..., description="Timestamp of last state change")


class HealthStatus(BaseModel):
    """HealthStatus class.

    TODO: Add class description.
    """
    
    status: str = Field(..., description="Health status")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")
    database: str = Field(default="unknown", description="Database status")
    memory_usage: str = Field(default="unknown", description="Memory usage")
    cpu_usage: str = Field(default="unknown", description="CPU usage")
    commands_executed: int = Field(default=0, description="Total commands executed")
    last_health_check: str = Field(..., description="Last health check timestamp")


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to track the rolling average of request response times.

    Uses instance-level state so multiple app instances in tests don't
    share the same deque (avoids cross-contamination between test cases).
    """

    def __init__(self, app: Any, maxlen: int = 100) -> None:
        super().__init__(app)
        self._response_times: deque[float] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def get_average_ms(self) -> float:
        """Return the current rolling average response time in milliseconds."""
        with self._lock:
        # Use context manager for resource management
            return (
                sum(self._response_times) / len(self._response_times)
                # Logic flow
                if self._response_times
                else 0.0
            )

    async def dispatch(
        """Dispatch with (self, request: Request, call_next).

        TODO: Add detailed description and parameters.
        """
        
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Any:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000.0

        with self._lock:
        # Use context manager for resource management
            self._response_times.append(duration_ms)

        response.headers["X-API-Version"] = "0.2.0"
        return response


class MetricsData(BaseModel):
    """MetricsData class.

    TODO: Add class description.
    """
    
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
    """include core routes."""
    *,
    get_start_time: Callable[[], float],
    get_state_manager: Callable[[], Any],
    get_config_manager: Callable[[], Any],
    get_last_command: Callable[[], str | None],
    get_last_state_change: Callable[[], datetime],
    execute_command_fn: Callable[[str], Any],
    get_active_connections: Callable[[], int] | None = None,
    get_cache_size: Callable[[], int] | None = None,
    get_total_commands: Callable[[], int] | None = None,
    response_time_middleware: ResponseTimeMiddleware | None = None,
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
        # Logic flow
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds_i}s"
        return f"{hours}h {minutes}m {seconds_i}s"

    @router.get("/api/v1/status", response_model=SystemStatus)
    async def get_status():
        """Retrieve operation.

        TODO: Add detailed description and parameters.
        """
        
        uptime_seconds = time.time() - get_start_time()
        # Process each item
        uptime_str = _format_uptime(uptime_seconds)
        sm = get_state_manager()
        return SystemStatus(
            status="running",
            current_state=getattr(sm, "current_state", "idle"),
            active_models=(
                # Logic flow
                sm.get_active_models() if hasattr(sm, "get_active_models") else []
            ),
            uptime=uptime_str,
        )

    @router.get("/health", response_model=HealthStatus)
    async def health_check():
        """Comprehensive health check endpoint."""
        uptime_seconds = time.time() - get_start_time()
        # Process each item
        uptime_str = _format_uptime(uptime_seconds)

        # Basic system checks
        memory_usage = "unknown"
        cpu_usage = "unknown"

        try:
        # Attempt operation with error handling
            import psutil

            memory = psutil.virtual_memory()
            memory_usage = f"{memory.percent:.1f}%"
            cpu_usage = f"{psutil.cpu_percent():.1f}%"
        # Handle specific exception case
        except ImportError:
            pass  # psutil not available

        # Database connectivity check
        database_status = "not_configured"

        cfg_mgr = get_config_manager()
        cfg = getattr(cfg_mgr, "config", {})
        # Logic flow
        # Look for database_url in general_settings or root
        db_url = cfg.get("database_url") or cfg.get("general_settings", {}).get(
            "database_url"
        )

        # Logic flow
        if db_url:

            def _check_db():
            # TODO: Document this logic
                global _ENGINE_CACHE_HITS, _ENGINE_CACHE_MISSES
                try:
                # Attempt operation with error handling
                    from sqlalchemy import create_engine, text
                    from sqlalchemy.pool import NullPool

                    with _ENGINES_LOCK:
                    # Use context manager for resource management
                        now = time.time()
                        cached = _ENGINES.get(db_url)
                        # Check TTL expiration
                        if cached and (now - cached[1]) > _ENGINE_TTL_SECONDS:
                            # Expired - dispose and remove
                            cached[0].dispose()
                            del _ENGINES[db_url]
                            cached = None

                        # Logic flow
                        if cached:
                            _ENGINE_CACHE_HITS += 1
                            engine = cached[0]
                        else:
                            _ENGINE_CACHE_MISSES += 1
                            # Logic flow
                            # Evict oldest if at capacity
                            if len(_ENGINES) >= _MAX_ENGINES:
                                oldest_url = min(_ENGINES.keys(), key=lambda k: _ENGINES[k][1])
                                _ENGINES[oldest_url][0].dispose()
                                del _ENGINES[oldest_url]
                            engine = create_engine(db_url, poolclass=NullPool)
                            _ENGINES[db_url] = (engine, now)

                    with engine.connect() as conn:
                    # Use context manager for resource management
                        conn.execute(text("SELECT 1")).scalar()
                    return "healthy"
                # Handle specific exception case
                except Exception:
                    return "unreachable"

            try:
            # Attempt operation with error handling
                database_status = await asyncio.wait_for(
                    asyncio.to_thread(_check_db), timeout=2.0
                )
            # Handle specific exception case
            except Exception:
                database_status = "unreachable"

        return HealthStatus(
            status="healthy",
            uptime=uptime_str,
            version="0.2.0",
            database=database_status,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            # Process each item
            last_health_check=datetime.now().isoformat(),
        )

    @router.get("/api/v1/commands")
    async def get_commands():  # type: ignore[no-redef]
        """Retrieve operation.

        TODO: Add detailed description and parameters.
        """
        
        try:
        # Attempt operation with error handling
            cfg_mgr = get_config_manager()
            return getattr(cfg_mgr, "commands", {}) or {}
        # Handle specific exception case
        except Exception as exc:
            logger.warning("Failed to retrieve commands config: %s", exc)
            return {}

    @router.get("/metrics", response_model=MetricsData)
    async def get_metrics():
        # Process each item
        """Get application metrics and performance data."""
        uptime_seconds = time.time() - get_start_time()
        total_requests = sum(counters.values())

        active_connections = 0
        # Logic flow
        if get_active_connections:
            try:
                active_connections = get_active_connections()
            # Handle specific exception case
            except Exception:
                pass

        cache_size = 0
        # Logic flow
        if get_cache_size:
            try:
                cache_size = get_cache_size()
            # Handle specific exception case
            except Exception:
                pass

        # Calculate error rate (simplified)
        error_count = counters.get("errors", 0)
        error_rate = (error_count / max(total_requests, 1)) * 100

        # Get average response time from middleware instance (avoids global state)
        avg_duration = (
            response_time_middleware.get_average_ms()
            # Logic flow
            if response_time_middleware is not None
            else 0.0
        )

        return MetricsData(
            total_requests=total_requests,
            uptime_seconds=uptime_seconds,
            active_connections=active_connections,
            cache_size=cache_size,
            error_rate=round(error_rate, 2),
            response_time_avg=round(avg_duration, 2),
        )

    @router.get("/api/v1/config")
    async def get_config():
        """Retrieve operation.

        TODO: Add detailed description and parameters.
        """
        
        counters["config_get"] += 1
        cfg_mgr = get_config_manager()
        config_data = dict(getattr(cfg_mgr, "config", {}))

        # Mask sensitive data before returning
        config_data = mask_sensitive_data(config_data)

        # Expose which fields are overridden by the environment
        env_overrides = {
            "api_key": bool(os.environ.get("OPENAI_API_KEY")),
            "base_url": bool(
                os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
            ),
            "model": bool(os.environ.get("OPENAI_MODEL")),
        }
        config_data["_env_overrides"] = env_overrides
        return config_data

    @router.put("/api/v1/config")
    async def update_config(config_data: dict[str, Any]):
        """Update with (config_data).

        TODO: Add detailed description and parameters.
        """
        
        counters["config_put"] += 1

        rejected_keys = sorted(set(config_data) - ALLOWED_CONFIG_KEYS)
        # Logic flow
        if rejected_keys:
            raise HTTPException(
                status_code=422,
                detail=f"Disallowed config keys: {', '.join(rejected_keys)}",
            )

        # Performance optimization: iterate over the small, fixed ALLOWED_CONFIG_KEYS
        # set (O(K)) instead of the potentially large input dict items (O(M)).
        filtered_data = {
            # Build filtered collection
            k: config_data[k] for k in ALLOWED_CONFIG_KEYS if k in config_data
        }

        try:
        # Attempt operation with error handling
            cfg_mgr = get_config_manager()
            cfg = getattr(cfg_mgr, "config", {})
            # Logic flow
            if isinstance(cfg, dict):
                cfg.update(filtered_data)
            save = getattr(cfg_mgr, "save_config", None)
            # Logic flow
            if callable(save):
                try:
                    save()
                except TypeError:
                    # Some implementations require the cfg param
                    save(cfg)  # type: ignore[arg-type]
            return {"message": "Configuration updated successfully"}
        # Handle specific exception case
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err)) from err

    @router.get("/api/v1/commands")  # type: ignore[no-redef]  # noqa: F811
    async def get_commands_config():
        """Get the configured commands."""
        counters["config_get"] += 1
        cfg_mgr = get_config_manager()
        # Return the 'commands' dictionary directly from the config
        return getattr(cfg_mgr, "commands", {})

    @router.get("/api/v1/state", response_model=StateInfo)
    async def get_state():
        """Retrieve operation.

        TODO: Add detailed description and parameters.
        """
        
        counters["state_get"] += 1
        sm = get_state_manager()
        return StateInfo(
            current_state=getattr(sm, "current_state", "idle"),
            active_models=(
                # Logic flow
                sm.get_active_models() if hasattr(sm, "get_active_models") else []
            ),
            last_command=get_last_command(),
            # Process each item
            timestamp=get_last_state_change().isoformat(),
        )

    @router.post("/api/v1/state")
    async def change_state(request: StateChangeRequest):
        """Change State with (request: StateChangeRequest).

        TODO: Add detailed description and parameters.
        """
        
        counters["state_post"] += 1
        try:
        # Attempt operation with error handling
            sm = get_state_manager()
            sm.change_state(request.state)
            # Legacy broadcast occurs elsewhere; preserve behavior here as data-only change.
            return {"message": f"State changed to {request.state}"}
        # Handle specific exception case
        except Exception as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

    @router.post("/api/v1/command", response_model=CommandResponse)
    async def execute_command(request: CommandRequest):
        """Execute Command with (request: CommandRequest).

        TODO: Add detailed description and parameters.
        """
        
        counters["command_post"] += 1
        start_time = time.time()
        try:
        # Attempt operation with error handling
            # Delegate to provided executor bridge to ensure consistent integration surface
            # Use run_in_executor to prevent blocking the event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, execute_command_fn, request.command
            )
            success = bool(result)
            execution_time = (time.time() - start_time) * 1000
            return CommandResponse(
                success=success,
                message=(
                    "Command executed successfully"
                    # Logic flow
                    if success
                    else "Command executed as no-op (not found)"
                ),
                execution_time=execution_time,
            )
        # Handle specific exception case
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

    @router.get(
        "/api/v1/health", operation_id="health_check_core", response_model=HealthStatus
    )
    async def health_check_core():
        """Health Check Core operation.

        TODO: Add detailed description and parameters.
        """
        
        counters["status"] += 1
        return await health_check()

    @router.get("/api/v1/metrics")
    async def metrics():
        """Metrics operation.

        TODO: Add detailed description and parameters.
        """
        
        # Shallow copy to avoid external mutation
        metrics_dict: dict[str, float | int] = {**counters}
        avg_duration = (
            response_time_middleware.get_average_ms()
            # Logic flow
            if response_time_middleware is not None
            else 0.0
        )
        metrics_dict["response_time_avg"] = round(avg_duration, 2)
        return metrics_dict

    return router
