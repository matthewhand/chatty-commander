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
import os
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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


class DiagnosticsData(BaseModel):
    disk_usage: dict[str, str] = Field(..., description="Disk usage of root partition")
    network_io: dict[str, int] = Field(..., description="Network I/O counters")
    thread_count: int = Field(..., description="Number of active threads")
    process_id: int = Field(..., description="Current process ID")


class HardwareInfo(BaseModel):
    gpu_available: bool = Field(..., description="Whether NVIDIA GPU is detected")
    gpu_name: str | None = Field(None, description="Name of the GPU if available")
    audio_input_devices: list[str] = Field(..., description="List of audio input devices")
    audio_output_devices: list[str] = Field(..., description="List of audio output devices")


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
            active_models=(
                sm.get_active_models() if hasattr(sm, "get_active_models") else []
            ),
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

        # Simple caching for system stats (1 second TTL)
        now = time.time()

        # Initialize cache attributes if not present
        if not hasattr(health_check, "_last_check"):
            health_check._last_check = 0.0
        if not hasattr(health_check, "_cached_stats"):
            health_check._cached_stats = None

        if now - health_check._last_check < 1.0 and health_check._cached_stats:
            memory_usage, cpu_usage = health_check._cached_stats
        else:
            def _get_system_stats():
                import psutil

                return psutil.virtual_memory().percent, psutil.cpu_percent()

            try:
                loop = asyncio.get_running_loop()
                mem_percent, cpu_percent = await loop.run_in_executor(
                    None, _get_system_stats
                )
                memory_usage = f"{mem_percent:.1f}%"
                cpu_usage = f"{cpu_percent:.1f}%"

                # Update cache
                health_check._cached_stats = (memory_usage, cpu_usage)
                health_check._last_check = now
            except ImportError:
                pass  # psutil not available
            except Exception:
                pass  # Other errors

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

    @router.get("/api/v1/diagnostics", response_model=DiagnosticsData)
    async def get_diagnostics():
        """Get detailed system diagnostics."""
        def _get_detailed_stats():
            import psutil
            import threading

            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            return {
                "disk_usage": {
                    "total": f"{disk.total / (1024**3):.1f} GB",
                    "used": f"{disk.used / (1024**3):.1f} GB",
                    "free": f"{disk.free / (1024**3):.1f} GB",
                    "percent": f"{disk.percent}%"
                },
                "network_io": {
                    "bytes_sent": net.bytes_sent,
                    "bytes_recv": net.bytes_recv,
                    "packets_sent": net.packets_sent,
                    "packets_recv": net.packets_recv
                },
                "thread_count": threading.active_count(),
                "process_id": os.getpid()
            }

        try:
            loop = asyncio.get_running_loop()
            stats = await loop.run_in_executor(None, _get_detailed_stats)
            return DiagnosticsData(**stats)
        except ImportError:
            raise HTTPException(status_code=501, detail="psutil not installed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/v1/hardware", response_model=HardwareInfo)
    async def get_hardware_info():
        """Discover available hardware (GPU, Audio)."""
        def _scan_hardware():
            import shutil
            import subprocess

            # GPU Check
            gpu_avail = False
            gpu_name = None
            if shutil.which("nvidia-smi"):
                try:
                    gpu_avail = True
                    # Try to get GPU name
                    res = subprocess.run(
                        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                        capture_output=True, text=True, timeout=1
                    )
                    if res.returncode == 0:
                        gpu_name = res.stdout.strip()
                except Exception:
                    pass

            # Audio Check
            inputs = []
            outputs = []
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                try:
                    for i in range(p.get_device_count()):
                        dev = p.get_device_info_by_index(i)
                        name = dev.get('name')
                        if dev.get('maxInputChannels') > 0:
                            inputs.append(name)
                        if dev.get('maxOutputChannels') > 0:
                            outputs.append(name)
                finally:
                    p.terminate()
            except ImportError:
                inputs = ["pyaudio_not_installed"]
                outputs = ["pyaudio_not_installed"]
            except Exception as e:
                inputs = [f"error: {str(e)}"]

            return {
                "gpu_available": gpu_avail,
                "gpu_name": gpu_name,
                "audio_input_devices": inputs,
                "audio_output_devices": outputs
            }

        try:
            loop = asyncio.get_running_loop()
            hw_info = await loop.run_in_executor(None, _scan_hardware)
            return HardwareInfo(**hw_info)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.websocket("/api/v1/ws/telemetry")
    async def telemetry_websocket(websocket: WebSocket):
        """
        Stream system telemetry (CPU, Mem, Uptime) every 2 seconds.
        """
        await websocket.accept()
        try:
            while True:
                # Reuse health check logic (cached) or fetch fresh
                # For streaming, we want regular updates, so let's call the logic directly
                # but slightly adapted to avoid redefining the inner function repeatedly.

                # Fetch fresh stats
                def _get_system_stats():
                    import psutil
                    return psutil.virtual_memory().percent, psutil.cpu_percent()

                try:
                    loop = asyncio.get_running_loop()
                    mem_percent, cpu_percent = await loop.run_in_executor(
                        None, _get_system_stats
                    )
                    memory_usage = f"{mem_percent:.1f}%"
                    cpu_usage = f"{cpu_percent:.1f}%"
                except Exception:
                    memory_usage = "unknown"
                    cpu_usage = "unknown"

                uptime_seconds = time.time() - get_start_time()

                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "uptime": _format_uptime(uptime_seconds),
                    "memory_usage": memory_usage,
                    "cpu_usage": cpu_usage,
                    "active_connections": get_active_connections() if get_active_connections else 0
                }

                await websocket.send_json(payload)
                await asyncio.sleep(2.0)

        except WebSocketDisconnect:
            pass
        except Exception:
            # Handle other connection errors
            try:
                await websocket.close()
            except Exception:
                pass

    @router.get("/api/v1/config")
    async def get_config():
        counters["config_get"] += 1
        cfg_mgr = get_config_manager()
        config_data = dict(getattr(cfg_mgr, "config", {}))
        
        # Expose which fields are overridden by the environment
        env_overrides = {
            "api_key": bool(os.environ.get("OPENAI_API_KEY")),
            "base_url": bool(os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")),
            "model": bool(os.environ.get("OPENAI_MODEL"))
        }
        config_data["_env_overrides"] = env_overrides
        return config_data

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
            active_models=(
                sm.get_active_models() if hasattr(sm, "get_active_models") else []
            ),
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
            # Delegate to provided executor bridge to ensure consistent integration surface
            success = bool(execute_command_fn(request.command))
            execution_time = (time.time() - start_time) * 1000
            return CommandResponse(
                success=success,
                message=(
                    "Command executed successfully"
                    if success
                    else "Command executed as no-op (not found)"
                ),
                execution_time=execution_time,
            )
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
    async def health_check_core():
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
