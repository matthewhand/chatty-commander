from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


def get_audio_devices() -> list[dict[str, Any]]:
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        devices = []
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get("deviceCount", 0)

        for i in range(0, numdevices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get("maxInputChannels", 0) > 0:
                devices.append(
                    {
                        "id": str(i),
                        "name": device_info.get("name", f"Input Device {i}"),
                        "type": "input",
                    }
                )
            if device_info.get("maxOutputChannels", 0) > 0:
                devices.append(
                    {
                        "id": str(i),
                        "name": device_info.get("name", f"Output Device {i}"),
                        "type": "output",
                    }
                )

        p.terminate()

        if not devices:
            return [{"id": "default", "name": "Default Device", "type": "input"}]
        return devices

    except ImportError:
        logger.warning("pyaudio not installed. Returning fallback audio devices.")
        return [{"id": "default", "name": "Default Device", "type": "input"}]
    except Exception as e:
        logger.error(f"Error fetching audio devices: {e}")
        return [{"id": "default", "name": "Default Device", "type": "input"}]


def include_audio_routes(get_config_manager: Callable[[], Any]) -> APIRouter:
    audio_router = APIRouter()

    @audio_router.get("/api/audio/devices")
    async def list_devices() -> list[dict[str, Any]]:
        return get_audio_devices()

    @audio_router.post("/api/audio/device")
    async def set_device(
        payload: dict[str, str] = Body(...),
        config_manager: Any = Depends(get_config_manager),
    ) -> dict[str, str]:
        device_id = payload.get("id")
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID is required")

        # Determine if we should store this as input or output device setting based on type
        device_type = payload.get("type", "input")

        # Verify the device actually exists
        devices = get_audio_devices()
        device_exists = any(d["id"] == device_id for d in devices)

        # Always allow "default" as a valid device ID even if not explicitly found
        if device_id != "default" and not device_exists:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found"
            )

        try:
            # Get the current configuration data dictionary
            config_data = getattr(config_manager, "config_data", {})

            # Ensure audio_settings dictionary exists
            if "audio_settings" not in config_data:
                config_data["audio_settings"] = {}

            # Update the appropriate setting
            if device_type == "input":
                config_data["audio_settings"]["input_device"] = device_id
            else:
                config_data["audio_settings"]["output_device"] = device_id

            # Save the updated configuration
            if hasattr(config_manager, "save_config"):
                config_manager.save_config()

            return {"status": "success", "active_device": device_id}

        except Exception as e:
            logger.error(f"Failed to set audio device: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to save audio settings"
            ) from e

    return audio_router
