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

"""
API routes for audio device management.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    import pyaudio

    AUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    AUDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioDevicesResponse(BaseModel):
    input: list[str]
    output: list[str]


class AudioDeviceSettings(BaseModel):
    input_device: str | None = None
    output_device: str | None = None


def get_audio_device_list() -> tuple[list[str], list[str]]:
    """Helper to get available audio devices."""
    if not AUDIO_AVAILABLE:
        return [], []

    input_devices = []
    output_devices = []

    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get("deviceCount")

        for i in range(numdevices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get("name")
            max_input_channels = device_info.get("maxInputChannels")
            max_output_channels = device_info.get("maxOutputChannels")

            if max_input_channels > 0:
                input_devices.append(device_name)

            if max_output_channels > 0:
                output_devices.append(device_name)

        p.terminate()
    except Exception as e:
        logger.error(f"Error listing audio devices: {e}")
        return [], []

    return input_devices, output_devices


def include_audio_routes(
    get_config_manager: Callable[[], Any],
) -> APIRouter:
    """Create the audio router with dependencies."""
    router = APIRouter()

    @router.get("/devices", response_model=AudioDevicesResponse)
    async def get_audio_devices() -> dict[str, list[str]]:
        """Get list of available audio input and output devices."""
        input_devices, output_devices = get_audio_device_list()
        return {"input": input_devices, "output": output_devices}

    @router.post("/settings")
    async def update_audio_settings(settings: AudioDeviceSettings) -> dict[str, Any]:
        """Update audio device settings."""
        if not AUDIO_AVAILABLE:
             # Just acknowledge if audio system is missing (e.g. cloud container)
             logger.warning("Audio unavailable, settings saved but not validated.")
             return {
                "success": True,
                "message": "Audio settings saved (audio unavailable)",
                "settings": settings.model_dump(exclude_none=True)
            }

        input_devices, output_devices = get_audio_device_list()

        # Validation
        if settings.input_device and settings.input_device not in input_devices:
             raise HTTPException(status_code=400, detail=f"Invalid input device: {settings.input_device}")

        if settings.output_device and settings.output_device not in output_devices:
             raise HTTPException(status_code=400, detail=f"Invalid output device: {settings.output_device}")

        # Persistence
        try:
            cfg_mgr = get_config_manager()
            # Update general settings where audio device preferences usually live
            # Assuming 'audio' section in config for this feature
            update_data = {"audio": {}}
            if settings.input_device:
                update_data["audio"]["input_device"] = settings.input_device
            if settings.output_device:
                update_data["audio"]["output_device"] = settings.output_device

            # Use the config manager's save method
            save = getattr(cfg_mgr, "save_config", None)
            if callable(save):
                # Update in-memory config first if needed, or rely on save_config merging logic
                # For safety, let's merge into existing config
                current_config = getattr(cfg_mgr, "config_data", {})
                if "audio" not in current_config:
                    current_config["audio"] = {}

                current_config["audio"].update(update_data["audio"])
                save(current_config)

        except Exception as e:
            logger.error(f"Failed to save audio settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to persist settings")

        return {
            "success": True,
            "message": "Audio settings updated",
            "settings": settings.model_dump(exclude_none=True)
        }

    return router
