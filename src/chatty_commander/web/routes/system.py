from __future__ import annotations

import platform
import sys
import time
from collections.abc import Callable
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

class SystemInfo(BaseModel):
    cpu_percent: Optional[float] = Field(None, description="Current CPU utilization as a percentage")
    memory_total_mb: Optional[int] = Field(None, description="Total physical memory in MB")
    memory_used_mb: Optional[int] = Field(None, description="Used physical memory in MB")
    memory_percent: Optional[float] = Field(None, description="Used memory as a percentage")
    disk_total_gb: Optional[float] = Field(None, description="Total disk space in GB")
    disk_used_gb: Optional[float] = Field(None, description="Used disk space in GB")
    disk_percent: Optional[float] = Field(None, description="Used disk space as a percentage")
    python_version: str = Field(..., description="Python version string")
    platform: str = Field(..., description="Platform identifier")
    uptime_seconds: float = Field(..., description="System uptime in seconds")

def include_system_routes(
    *,
    get_start_time: Callable[[], float],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/system/info", response_model=SystemInfo)
    async def get_system_info():
        uptime_seconds = time.time() - get_start_time()

        info = SystemInfo(
            python_version=sys.version.split(" ")[0],
            platform=platform.platform(),
            uptime_seconds=uptime_seconds,
        )

        try:
            import psutil

            # CPU
            info.cpu_percent = psutil.cpu_percent(interval=None)

            # Memory
            mem = psutil.virtual_memory()
            info.memory_total_mb = int(mem.total / (1024 * 1024))
            info.memory_used_mb = int(mem.used / (1024 * 1024))
            info.memory_percent = mem.percent

            # Disk
            disk = psutil.disk_usage("/")
            info.disk_total_gb = round(disk.total / (1024 * 1024 * 1024), 2)
            info.disk_used_gb = round(disk.used / (1024 * 1024 * 1024), 2)
            info.disk_percent = disk.percent

        except ImportError:
            pass

        return info

    return router
