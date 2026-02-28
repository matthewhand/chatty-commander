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

class AudioDevices(BaseModel):
    input: list[str] = Field(default_factory=list)
    output: list[str] = Field(default_factory=list)

class AudioDeviceRequest(BaseModel):
    device_id: str

def include_audio_routes(
    *,
    get_config_manager: Any,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/audio/devices", response_model=AudioDevices)
    async def get_audio_devices():
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            input_devices = []
            output_devices = []
            try:
                info = p.get_host_api_info_by_index(0)
                numdevices = info.get('deviceCount') or 0

                for i in range(0, numdevices):
                    device_info = p.get_device_info_by_host_api_device_index(0, i)
                    if (device_info.get('maxInputChannels') or 0) > 0:
                        input_devices.append(device_info.get('name'))
                    if (device_info.get('maxOutputChannels') or 0) > 0:
                        output_devices.append(device_info.get('name'))
            finally:
                p.terminate()
            return AudioDevices(input=input_devices, output=output_devices)
        except ImportError:
            # Fallback for environments without PyAudio or audio hardware (e.g., CI/Container)
            return AudioDevices(
                input=["Mock Microphone 1", "Mock Microphone 2"],
                output=["Mock Speaker 1", "Mock Speaker 2"]
            )
        except Exception as e:
            logger.warning(f"Failed to list audio devices: {e}")
            return AudioDevices()

    @router.post("/api/v1/audio/device")
    async def set_audio_device(request: AudioDeviceRequest):
        try:
            cfg_mgr = get_config_manager()
            logger.info(f"Setting audio device to: {request.device_id}")

            # Attempt to save if structure exists
            if hasattr(cfg_mgr, "config"):
                if "audio" not in cfg_mgr.config:
                    cfg_mgr.config["audio"] = {}
                cfg_mgr.config["audio"]["device"] = request.device_id

                if hasattr(cfg_mgr, "save_config"):
                    cfg_mgr.save_config()

            return {"success": True, "device": request.device_id}
        except Exception as e:
            logger.error(f"Failed to set audio device: {e}")
            raise HTTPException(status_code=500, detail="Failed to update audio device configuration")

    return router
