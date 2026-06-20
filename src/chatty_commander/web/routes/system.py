from __future__ import annotations

import logging
import os
import platform
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class EnvVarInfo(BaseModel):
    name: str = Field(..., description="Environment variable name")
    set: bool = Field(..., description="Whether the variable is currently set")
    description: str = Field(..., description="Human-readable description of the variable")
    default: str | None = Field(None, description="Default value when not set")
    required: bool = Field(False, description="Whether the variable is required")


# Recognised environment variables: (description, default, required)
_ENV_VAR_CATALOG: dict[str, tuple[str, str | None, bool]] = {
    # LLM / OpenAI
    "OPENAI_API_KEY": ("OpenAI API key for LLM access", None, False),
    "OPENAI_BASE_URL": ("Custom base URL for OpenAI-compatible API", "https://api.openai.com/v1", False),
    "OPENAI_API_BASE": ("Legacy base URL for OpenAI-compatible API (fallback for OPENAI_BASE_URL)", "https://api.openai.com/v1", False),
    "OPENAI_MODEL": ("Default OpenAI model to use", "gpt-3.5-turbo", False),
    # Ollama
    "OLLAMA_HOST": ("Host address for a local Ollama instance", "ollama:11434", False),
    # LLM manager
    "LLM_BACKEND": ("Preferred LLM backend (e.g. openai, ollama)", None, False),
    # Agents
    "CHATTY_AGENTS_STORE": ("Path to the agents store JSON file", "~/.chatty_commander/agents.json", False),
    # Bridge / API endpoints
    "CHATTY_BRIDGE_TOKEN": ("Authentication token for the web-server bridge", None, False),
    "CHATBOT_ENDPOINT": ("Override URL for the chatbot API endpoint", None, False),
    "HOME_ASSISTANT_ENDPOINT": ("Override URL for the Home Assistant API endpoint", None, False),
    # General settings
    "CHATCOMM_DEBUG": ("Enable debug mode (true/yes/1)", None, False),
    "CHATCOMM_DEFAULT_STATE": ("Default application state on startup", "idle", False),
    "CHATCOMM_INFERENCE_FRAMEWORK": ("Inference framework to use (e.g. onnx)", "onnx", False),
    "CHATCOMM_START_ON_BOOT": ("Start application on system boot (true/yes/1)", None, False),
    "CHATCOMM_CHECK_FOR_UPDATES": ("Enable automatic update checks (true/yes/1)", None, False),
    # CLI
    "CHATCOMM_HOST": ("Host address for the CLI to connect to", None, False),
    "CHATCOMM_PORT": ("Port for the CLI to connect to", None, False),
    "CHATCOMM_LOG_LEVEL": ("Log level for the CLI (e.g. info, debug)", "info", False),
    # Logging
    "LOG_LEVEL": ("Application log level", "INFO", False),
    "LOG_FORMAT": ("Log output format (plain or json)", "plain", False),
    # Misc
    "CC_FAST": ("Enable fast/reduced test mode when set to 1", None, False),
    "XDG_CONFIG_HOME": ("XDG base directory for user configuration", "~/.config", False),
}

# Recognised environment variables and their descriptions
_ENV_VAR_DESCRIPTIONS: dict[str, str] = {
    "OPENAI_API_KEY": "OpenAI API key for LLM access",
    "OPENAI_BASE_URL": "Custom base URL for OpenAI-compatible API",
    "OPENAI_API_BASE": "Legacy base URL for OpenAI-compatible API",
    "OPENAI_MODEL": "Default OpenAI model to use",
    "CHATTY_AGENTS_STORE": "Path to the agents store directory",
    "OLLAMA_HOST": "Host address for a local Ollama instance",
}


class SystemInfo(BaseModel):
    cpu_percent: float | None = Field(None, description="Current CPU utilization as a percentage")
    memory_total_mb: int | None = Field(None, description="Total physical memory in MB")
    memory_used_mb: int | None = Field(None, description="Used physical memory in MB")
    memory_percent: float | None = Field(None, description="Used memory as a percentage")
    disk_total_gb: float | None = Field(None, description="Total disk space in GB")
    disk_used_gb: float | None = Field(None, description="Used disk space in GB")
    disk_percent: float | None = Field(None, description="Used disk space as a percentage")
    python_version: str = Field(..., description="Python version string")
    platform: str = Field(..., description="Platform identifier")
    architecture: str = Field(..., description="Machine architecture")
    pid: int = Field(..., description="Current process ID")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    env_vars: list[EnvVarInfo] = Field(
        default_factory=list,
        description="Recognised environment variables and whether they are set",
    )


class ActionResponse(BaseModel):
    """Generic success response for control/backup/restore actions."""

    model_config = ConfigDict(extra="allow")  # allow action-specific fields like data, applied, restored_from etc.

    success: bool = Field(True, description="Whether the action was accepted")
    message: str = Field(..., description="Human-readable result or status")
    # Optional fields populated by specific actions
    theme: str | None = Field(None, description="For theme actions")
    backup_id: str | None = Field(None, description="For backup actions")
    timestamp: float | None = Field(None, description="For timestamped actions")
    preferences: dict[str, Any] | None = Field(None, description="Echo of updated prefs")


def include_system_routes(
    *,
    get_start_time: Callable[[], float],
    get_config_manager: Callable[[], Any] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/system/info", response_model=SystemInfo)
    async def get_system_info():
        uptime_seconds = time.time() - get_start_time()

        env_vars = [
            EnvVarInfo(
                name=name,
                set=(name in os.environ),
                description=desc,
                default=default,
                required=required,
            )
            for name, (desc, default, required) in _ENV_VAR_CATALOG.items()
        ] + [
            # Only include description-only vars that aren't already in the
            # catalog, otherwise the response carries duplicate entries (every
            # _ENV_VAR_DESCRIPTIONS key currently also lives in the catalog).
            EnvVarInfo(name=name, set=(name in os.environ), description=desc, default=None, required=False)
            for name, desc in _ENV_VAR_DESCRIPTIONS.items()
            if name not in _ENV_VAR_CATALOG
        ]

        info = SystemInfo(
            cpu_percent=None,
            memory_total_mb=None,
            memory_used_mb=None,
            memory_percent=None,
            disk_total_gb=None,
            disk_used_gb=None,
            disk_percent=None,
            python_version=sys.version,
            platform=platform.platform(),
            architecture=platform.machine(),
            pid=os.getpid(),
            uptime_seconds=uptime_seconds,
            env_vars=env_vars,
        )

        try:
            import psutil

            # CPU — use interval=0.1 to avoid the misleading 0.0 on first call
            info.cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory
            mem = psutil.virtual_memory()
            info.memory_total_mb = int(mem.total / (1024 * 1024))
            info.memory_used_mb = int(mem.used / (1024 * 1024))
            info.memory_percent = mem.percent

            # Disk — use cross-platform root path detection
            root_path = Path(sys.executable).anchor  # e.g. "/" on Unix, "C:\\" on Windows
            disk = psutil.disk_usage(root_path)
            info.disk_total_gb = round(disk.total / (1024 * 1024 * 1024), 2)
            info.disk_used_gb = round(disk.used / (1024 * 1024 * 1024), 2)
            info.disk_percent = disk.percent

        except ImportError:
            pass

        return info

    # NOTE: GET/POST /api/themes + /api/theme and GET/PUT /api/preferences are
    # NOT registered here — they are owned by web/routes/themes.py and
    # web/routes/preferences.py, which register first in register_shared_routers
    # (so they win FastAPI dispatch) and carry the real validation/allow-list.
    # Duplicating them here only produced shadowed dead code + duplicate
    # OpenAPI operation IDs (and was the root of the round-7 "shadowed
    # allow-list" bug). ALLOWED_PREF_KEYS below is still used by /api/restore.

    # --- Backup / Restore (stubs, functional enough for UI; persist config snapshot) ---
    @router.post("/api/backup", response_model=ActionResponse)
    async def create_backup():
        # Returns a snapshot of config for frontend to save/download if desired.
        # (For full file backup/restore of arbitrary, use /api/v1/models/ or external.)
        backup_data: dict[str, Any] = {}
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                backup_data = getattr(cfg_mgr, "config", {}) or {}
            except Exception as e:
                logger.warning(f"Backup snapshot read failed: {e}")
        return {
            "success": True,
            "message": "Backup created (config snapshot)",
            "backup_id": f"backup-{int(time.time())}",
            "timestamp": time.time(),
            "data": backup_data,  # included for restore payload compatibility
        }

    @router.post("/api/restore", response_model=ActionResponse)
    async def restore_backup(payload: dict[str, Any] | None = None):
        payload = payload or {}
        applied = False
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                data = payload.get("data") if isinstance(payload, dict) else None
                data = data if isinstance(data, dict) else (payload if isinstance(payload, dict) else {})
                if hasattr(cfg_mgr, "config"):
                    # SECURITY: same allow-list filter as PUT /api/preferences —
                    # a restore payload must not be able to overwrite arbitrary
                    # config keys (auth, web_server, ...).
                    for k, v in data.items():
                        if k in ALLOWED_PREF_KEYS:
                            cfg_mgr.config[k] = v
                    if hasattr(cfg_mgr, "save_config"):
                        cfg_mgr.save_config()
                    applied = True
            except Exception as e:
                logger.warning(f"Failed to apply restore: {e}")
        return {"success": True, "message": "Restore completed (config applied where possible)", "restored_from": payload, "applied": applied}

    # --- System control (restart/shutdown are graceful acks; no real process kill) ---
    # Protected by AuthMiddleware (see middleware/auth.py): /api/* paths require valid X-API-Key
    # unless WebModeServer(..., no_auth=True) or server.create_app used in --no-auth/dev mode.
    # These are intentionally non-destructive stubs (return 200 + ack); real shutdown/restart
    # would be orchestrated by caller/CLI if needed.
    @router.post("/api/system/restart", response_model=ActionResponse)
    async def system_restart():
        logger.info("System restart requested via API (stub - no actual restart performed)")
        return {"success": True, "message": "Restart signal accepted (stub in this environment)"}

    @router.post("/api/system/shutdown", response_model=ActionResponse)
    async def system_shutdown():
        logger.info("System shutdown requested via API (stub - no actual shutdown performed)")
        return {"success": True, "message": "Shutdown signal accepted (stub in this environment)"}

    return router


# Allowed top level keys for permissive preference updates (extends core ALLOWED but here local)
ALLOWED_PREF_KEYS = {"ui", "general", "audio_settings", "voice", "logging", "voice_only", "default_state"}
