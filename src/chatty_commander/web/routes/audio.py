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

"""Audio configuration routes."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    import pyaudio
except ImportError:
    pyaudio = None

logger = logging.getLogger(__name__)

router = APIRouter()


class AudioDevicesResponse(BaseModel):
    input: list[str] = Field(description="List of input device names")
    output: list[str] = Field(description="List of output device names")


class AudioDeviceUpdate(BaseModel):
    device_id: str = Field(description="Name or ID of the device to select")


@router.get("/api/audio/devices", response_model=AudioDevicesResponse)
async def get_audio_devices():
    """Get available audio input and output devices."""
    if not pyaudio:
        logger.warning("PyAudio not installed; returning empty device lists")
        return AudioDevicesResponse(input=[], output=[])

    try:
        p = pyaudio.PyAudio()
        input_devices = []
        output_devices = []
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get("deviceCount")

        for i in range(0, numdevices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get("name")
            max_input_channels = device_info.get("maxInputChannels")
            max_output_channels = device_info.get("maxOutputChannels")

            if max_input_channels > 0:
                input_devices.append(device_name)
            if max_output_channels > 0:
                output_devices.append(device_name)

        p.terminate()
        return AudioDevicesResponse(input=input_devices, output=output_devices)
    except Exception as e:
        logger.error(f"Error fetching audio devices: {e}")
        # Return empty lists on error rather than failing the request
        return AudioDevicesResponse(input=[], output=[])


@router.post("/api/audio/device")
async def set_audio_device(update: AudioDeviceUpdate):
    """Set the active audio input device.

    Persists the setting to the configuration file using the global config manager.
    """
    from chatty_commander.app.config import Config

    # In a real app we'd inject this, but for now we load/save the singleton file
    # Config is designed to reload from disk, so we can instantiate a fresh one to edit
    try:
        cfg = Config()
        # Ensure voice section exists
        if "voice" not in cfg.config_data:
            cfg.config_data["voice"] = {}

        cfg.config_data["voice"]["input_device"] = update.device_id
        cfg.save_config()

        logger.info(f"Updated audio input device to: {update.device_id}")
        return {"status": "updated", "device": update.device_id}
    except Exception as e:
        logger.error(f"Failed to save audio config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
