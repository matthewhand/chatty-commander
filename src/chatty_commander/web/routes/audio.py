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

# Module-level fallback state for the selected device, used when no config
# manager is available (or persisting through it fails).
_selected_device: dict[str, str | None] = {"device_id": None}


class AudioDevices(BaseModel):
    input: list[str] = Field(default_factory=list)
    output: list[str] = Field(default_factory=list)
    # False when no audio backend (pyaudio) or hardware is available.
    available: bool = True


class AudioDeviceRequest(BaseModel):
    device_id: str


def _list_audio_devices() -> AudioDevices:
    """Enumerate audio devices via pyaudio, degrading gracefully.

    Returns empty device lists with ``available=False`` when pyaudio is not
    installed or device enumeration fails (e.g. headless CI containers).
    """
    try:
        import pyaudio
    except ImportError:
        logger.info("pyaudio is not installed; reporting no audio devices")
        return AudioDevices(available=False)

    try:
        p = pyaudio.PyAudio()
        input_devices: list[str] = []
        output_devices: list[str] = []
        try:
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get("deviceCount") or 0

            for i in range(0, numdevices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                name = device_info.get("name")
                if name is None:
                    continue
                if (device_info.get("maxInputChannels") or 0) > 0:
                    input_devices.append(name)
                if (device_info.get("maxOutputChannels") or 0) > 0:
                    output_devices.append(name)
        finally:
            p.terminate()
        return AudioDevices(input=input_devices, output=output_devices, available=True)
    except Exception as e:  # pragma: no cover - depends on host audio stack
        logger.warning(f"Failed to list audio devices: {e}")
        return AudioDevices(available=False)


def include_audio_routes(
    *,
    get_config_manager: Any,
) -> APIRouter:
    router = APIRouter()

    # Registered on both the legacy/v1 path (used by ConfigurationPage.tsx)
    # and the unversioned path (used by apiService.js / AudioSettingsPage).
    @router.get("/api/audio/devices", response_model=AudioDevices)
    @router.get("/api/v1/audio/devices", response_model=AudioDevices)
    async def get_audio_devices():
        return _list_audio_devices()

    @router.post("/api/audio/device")
    @router.post("/api/v1/audio/device")
    async def set_audio_device(request: AudioDeviceRequest):
        device_id = request.device_id.strip()
        if not device_id:
            raise HTTPException(
                status_code=400, detail="device_id must be a non-empty string"
            )

        logger.info(f"Setting audio device to: {device_id}")
        # Always remember the selection in module state so the choice survives
        # even when no config manager is wired up.
        _selected_device["device_id"] = device_id

        persisted = False
        try:
            cfg_mgr = get_config_manager() if callable(get_config_manager) else None
            if cfg_mgr is not None and isinstance(getattr(cfg_mgr, "config", None), dict):
                cfg_mgr.config.setdefault("audio", {})["device"] = device_id
                if hasattr(cfg_mgr, "save_config"):
                    cfg_mgr.save_config()
                persisted = True
        except Exception as e:
            # Degrade gracefully: the selection is kept in module state above.
            logger.warning(f"Failed to persist audio device selection: {e}")

        return {"success": True, "device": device_id, "persisted": persisted}

    return router
