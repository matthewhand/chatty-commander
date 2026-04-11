from __future__ import annotations

import os
import platform
import sys
import time
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field


class EnvVarInfo(BaseModel):
    name: str = Field(..., description="Environment variable name")
    set: bool = Field(..., description="Whether the variable is currently set")
    description: str = Field(..., description="Human-readable description of the variable")


# Recognised environment variables and their descriptions
_ENV_VAR_DESCRIPTIONS: dict[str, str] = {
    "OPENAI_API_KEY": "OpenAI API key for LLM access",
    "OPENAI_BASE_URL": "Custom base URL for OpenAI-compatible API",
    "OPENAI_API_BASE": "Legacy base URL for OpenAI-compatible API",
    "OPENAI_MODEL": "Default OpenAI model to use",
    "CHATTY_AGENTS_STORE": "Path to the agents store directory",
    "OLLAMA_HOST": "Host address for a local Ollama instance",
}


class SystemInfo(BaseModel):
    cpu_percent: float | None = Field(None, description="Current CPU utilization as a percentage")
    memory_total_mb: int | None = Field(None, description="Total physical memory in MB")
    memory_used_mb: int | None = Field(None, description="Used physical memory in MB")
    memory_percent: float | None = Field(None, description="Used memory as a percentage")
    disk_total_gb: float | None = Field(None, description="Total disk space in GB")
    disk_used_gb: float | None = Field(None, description="Used disk space in GB")
    disk_percent: float | None = Field(None, description="Used disk space as a percentage")
    python_version: str = Field(..., description="Python version string")
    platform: str = Field(..., description="Platform identifier")
    architecture: str = Field(..., description="Machine architecture")
    pid: int = Field(..., description="Current process ID")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    env_vars: list[EnvVarInfo] = Field(
        default_factory=list,
        description="Recognised environment variables and whether they are set",
    )

def include_system_routes(
    *,
    get_start_time: Callable[[], float],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/system/info", response_model=SystemInfo)
    async def get_system_info():
        uptime_seconds = time.time() - get_start_time()

        env_vars = [
            EnvVarInfo(name=name, set=(name in os.environ), description=desc)
            for name, desc in _ENV_VAR_DESCRIPTIONS.items()
        ]

        info = SystemInfo(
            python_version=sys.version,
            platform=platform.platform(),
            architecture=platform.machine(),
            pid=os.getpid(),
            uptime_seconds=uptime_seconds,
            env_vars=env_vars,
        )

        try:
            import psutil

            # CPU — use interval=0.1 to avoid the misleading 0.0 on first call
            info.cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory
            mem = psutil.virtual_memory()
            info.memory_total_mb = int(mem.total / (1024 * 1024))
            info.memory_used_mb = int(mem.used / (1024 * 1024))
            info.memory_percent = mem.percent

            # Disk — use cross-platform root path detection
            root_path = Path(sys.executable).anchor  # e.g. "/" on Unix, "C:\\" on Windows
            disk = psutil.disk_usage(root_path)
            info.disk_total_gb = round(disk.total / (1024 * 1024 * 1024), 2)
            info.disk_used_gb = round(disk.used / (1024 * 1024 * 1024), 2)
            info.disk_percent = disk.percent

        except ImportError:
            pass

        return info

    return router
