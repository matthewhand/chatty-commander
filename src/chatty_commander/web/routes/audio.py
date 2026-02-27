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

# Optional: try to import pyaudio or sounddevice
try:
    import pyaudio
except ImportError:
    pyaudio = None


class AudioDevice(BaseModel):
    id: int
    name: str
    channels: int
    sample_rate: float


class AudioDevicesResponse(BaseModel):
    input: list[str]
    output: list[str]
    default_input: str | None = None
    default_output: str | None = None


class SetDeviceRequest(BaseModel):
    device_id: str = Field(..., description="Device name or ID to set as active")
    kind: str = Field("input", pattern="^(input|output)$", description="Device type")


router = APIRouter()
logger = logging.getLogger(__name__)


def _get_pyaudio_devices() -> tuple[list[str], list[str]]:
    """Helper to enumerate devices via PyAudio."""
    input_devices = []
    output_devices = []

    if not pyaudio:
        return ["Default Input"], ["Default Output"]

    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            name = device_info.get('name')

            if device_info.get('maxInputChannels') > 0:
                input_devices.append(name)

            if device_info.get('maxOutputChannels') > 0:
                output_devices.append(name)

        p.terminate()
    except Exception as e:
        logger.error(f"Error enumerating audio devices: {e}")
        return ["Error enumerating devices"], ["Error enumerating devices"]

    return input_devices, output_devices


@router.get("/api/audio/devices", response_model=AudioDevicesResponse)
async def get_audio_devices():
    """Get list of available audio input and output devices."""
    input_devs, output_devs = _get_pyaudio_devices()
    return AudioDevicesResponse(
        input=input_devs,
        output=output_devs,
        default_input=input_devs[0] if input_devs else None,
        default_output=output_devs[0] if output_devs else None
    )


@router.post("/api/audio/device")
async def set_audio_device(request: SetDeviceRequest):
    """Set the active audio device."""
    # In a real implementation, this would update the config and potentially
    # restart audio streams. For now, we just acknowledge the request.
    logger.info(f"Setting {request.kind} device to: {request.device_id}")
    return {"status": "ok", "message": f"{request.kind} device set to {request.device_id}"}
