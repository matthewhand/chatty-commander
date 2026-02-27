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

class AudioDevicesResponse(BaseModel):
    input: list[str] = Field(..., description="List of input devices")
    output: list[str] = Field(..., description="List of output devices")

class SetAudioDeviceRequest(BaseModel):
    device_id: str = Field(..., description="Device ID or Name to set")

@router.get("/api/audio/devices", response_model=AudioDevicesResponse)
async def get_audio_devices():
    """Get list of available audio input and output devices."""
    input_devices = []
    output_devices = []

    try:
        import pyaudio
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                input_devices.append(p.get_device_info_by_host_api_device_index(0, i).get('name'))
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
                output_devices.append(p.get_device_info_by_host_api_device_index(0, i).get('name'))
        p.terminate()
    except ImportError:
        logger.warning("PyAudio not available. Returning mock devices.")
        input_devices = ["Mock Microphone 1", "Mock Microphone 2"]
        output_devices = ["Mock Speaker 1", "Mock Headphones"]
    except Exception as e:
        logger.error(f"Error listing audio devices: {e}")
        # Return empty list on error
        pass

    return AudioDevicesResponse(input=input_devices, output=output_devices)

@router.post("/api/audio/device")
async def set_audio_device(request: SetAudioDeviceRequest):
    """Set the active audio input/output device (placeholder logic)."""
    # Logic to set the device would go here.
    # Since this often requires restarting the stream or re-initializing PyAudio in the main process,
    # we might need to communicate with a manager.
    # For now, we just log it.
    logger.info(f"Requested to set audio device to: {request.device_id}")
    return {"message": f"Audio device set to {request.device_id}"}
