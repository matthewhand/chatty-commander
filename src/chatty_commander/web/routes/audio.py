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


class AudioDeviceList(BaseModel):
    input: list[str] = Field(default_factory=list, description="List of input device names")
    output: list[str] = Field(default_factory=list, description="List of output device names")


class AudioDeviceUpdate(BaseModel):
    device_id: str = Field(..., description="Device name/ID to select")


def _get_pyaudio_devices() -> tuple[list[str], list[str]]:
    """
    Enumerate audio devices using PyAudio if available.
    Returns (input_devices, output_devices).
    """
    inputs = []
    outputs = []

    try:
        import pyaudio
        p = pyaudio.PyAudio()
        try:
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get("deviceCount", 0)

            for i in range(num_devices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                name = device_info.get("name")
                max_input = device_info.get("maxInputChannels")
                max_output = device_info.get("maxOutputChannels")

                if max_input > 0:
                    inputs.append(name)
                if max_output > 0:
                    outputs.append(name)
        finally:
            p.terminate()

    except ImportError:
        logger.warning("PyAudio not available; returning empty device lists")
    except Exception as e:
        logger.error(f"Error enumerating audio devices: {e}")

    return inputs, outputs


@router.get("/devices", response_model=AudioDeviceList)
async def get_audio_devices():
    """Get available audio input and output devices."""
    inputs, outputs = _get_pyaudio_devices()
    return AudioDeviceList(input=inputs, output=outputs)


@router.post("/device")
async def set_audio_device(request: AudioDeviceUpdate):
    """
    Set the preferred audio input/output device.

    Note: Currently this just acknowledges the request.
    Actual device selection logic would need to be wired into the
    voice pipeline config.
    """
    # TODO: Persist this selection to Config
    logger.info(f"Client requested audio device: {request.device_id}")
    return {"status": "success", "message": f"Device {request.device_id} selected"}
