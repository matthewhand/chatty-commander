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

router = APIRouter()


class AudioDevicesResponse(BaseModel):
    input: list[str]
    output: list[str]


class AudioDeviceSettings(BaseModel):
    input_device: str | None = None
    output_device: str | None = None


@router.get("/devices", response_model=AudioDevicesResponse)
async def get_audio_devices() -> dict[str, list[str]]:
    """Get list of available audio input and output devices."""
    if not AUDIO_AVAILABLE:
        return {"input": [], "output": []}

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
        return {"input": [], "output": []}

    return {"input": input_devices, "output": output_devices}


@router.post("/settings")
async def update_audio_settings(settings: AudioDeviceSettings) -> dict[str, Any]:
    """Update audio device settings."""
    # In a real implementation, this would persist the settings to configuration
    # For now, we just acknowledge the request and log it
    logger.info(f"Updating audio settings: input={settings.input_device}, output={settings.output_device}")

    # We could also validate that the devices actually exist here

    return {
        "success": True,
        "message": "Audio settings updated",
        "settings": {
            "input_device": settings.input_device,
            "output_device": settings.output_device
        }
    }
