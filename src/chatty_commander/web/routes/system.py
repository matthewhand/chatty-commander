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

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

class SystemInfoResponse(BaseModel):
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    os_info: str = Field(..., description="Operating system information")
    python_version: str = Field(..., description="Python version")

class PreferencesResponse(BaseModel):
    theme: str = Field(..., description="UI Theme")
    notifications_enabled: bool = Field(..., description="Notifications enabled")
    volume: int = Field(..., description="Master volume")

class UpdatePreferencesRequest(BaseModel):
    theme: str | None = Field(default=None, description="UI Theme")
    notifications_enabled: bool | None = Field(default=None, description="Notifications enabled")
    volume: int | None = Field(default=None, description="Master volume")

@router.get("/api/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    """Get detailed system information."""
    import psutil
    import platform
    import sys

    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    os_info = f"{platform.system()} {platform.release()}"
    py_ver = sys.version.split(" ")[0]

    return SystemInfoResponse(
        cpu_usage=cpu,
        memory_usage=mem,
        disk_usage=disk,
        os_info=os_info,
        python_version=py_ver
    )

@router.get("/api/preferences", response_model=PreferencesResponse)
async def get_preferences():
    """Get current user preferences."""
    # Placeholder: Retrieve from config/db
    return PreferencesResponse(
        theme="dark",
        notifications_enabled=True,
        volume=80
    )

@router.put("/api/preferences")
async def update_preferences(prefs: UpdatePreferencesRequest):
    """Update user preferences."""
    # Logic to save preferences
    logger.info(f"Updated preferences: {prefs}")
    return {"message": "Preferences updated"}

@router.post("/api/system/restart")
async def restart_system():
    """Restart the application (or system - careful!)."""
    # Just a placeholder log for now
    logger.warning("System restart requested via API.")
    return {"message": "Restart initiated"}

@router.post("/api/system/shutdown")
async def shutdown_system():
    """Shutdown the application."""
    # Placeholder
    logger.warning("System shutdown requested via API.")
    return {"message": "Shutdown initiated"}
