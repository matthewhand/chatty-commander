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


def include_audio_routes(config_manager: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/audio/devices", response_model=AudioDevicesResponse)
    async def get_audio_devices():
        """Get list of available audio input and output devices."""
        loop = asyncio.get_running_loop()
        # Offload blocking PyAudio call to thread executor
        input_devs, output_devs = await loop.run_in_executor(None, _get_pyaudio_devices)

        # Retrieve saved preferences
        audio_cfg = config_manager.config_data.get("audio", {})
        saved_input = audio_cfg.get("input_device")
        saved_output = audio_cfg.get("output_device")

        # Fallback logic:
        # 1. Use saved preference if available and valid (in current list)
        # 2. Use first available device
        default_input = saved_input if saved_input in input_devs else (input_devs[0] if input_devs else None)
        default_output = saved_output if saved_output in output_devs else (output_devs[0] if output_devs else None)

        return AudioDevicesResponse(
            input=input_devs,
            output=output_devs,
            default_input=default_input,
            default_output=default_output
        )


    @router.post("/api/audio/device")
    async def set_audio_device(request: SetDeviceRequest):
        """Set the active audio device."""
        loop = asyncio.get_running_loop()
        # Validate device existence via thread pool
        input_devs, output_devs = await loop.run_in_executor(None, _get_pyaudio_devices)

        target_list = input_devs if request.kind == "input" else output_devs

        if request.device_id not in target_list:
             # Allow setting "Default Input"/"Default Output" if pyaudio is missing as a special case for tests/mocking
             if not pyaudio and request.device_id in ["Default Input", "Default Output"]:
                 pass
             else:
                raise HTTPException(status_code=400, detail=f"Device '{request.device_id}' not found in available {request.kind} devices")

        # Update configuration
        if "audio" not in config_manager.config_data:
            config_manager.config_data["audio"] = {}

        key = "input_device" if request.kind == "input" else "output_device"
        config_manager.config_data["audio"][key] = request.device_id

        # Save config asynchronously if possible, or offload
        if hasattr(config_manager, "save_config"):
             await loop.run_in_executor(None, config_manager.save_config)

        logger.info(f"Setting {request.kind} device to: {request.device_id}")
        return {"status": "ok", "message": f"{request.kind} device set to {request.device_id}"}

    return router
