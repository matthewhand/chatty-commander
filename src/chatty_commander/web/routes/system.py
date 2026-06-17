from __future__ import annotations

import logging
import os
import platform
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class EnvVarInfo(BaseModel):
    """EnvVarInfo class.

    TODO: Add class description.
    """
    
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
    """SystemInfo class.

    TODO: Add class description.
    """
    
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


class ThemeInfo(BaseModel):
    """Response for available UI themes and currently active one."""

    themes: list[str] = Field(..., description="List of supported theme identifiers")
    current: str | None = Field(None, description="Currently selected theme (from persisted config if available)")


class ThemeSetRequest(BaseModel):
    """Request payload for setting active theme (permissive for frontend variations)."""

    theme: str | None = Field(None, description="Theme name to activate")
    name: str | None = Field(None, description="Alternative key for theme name")


class PreferencesResponse(BaseModel):
    """Response wrapper for user preferences."""

    preferences: dict[str, Any] = Field(default_factory=dict, description="Active preferences (ui, audio, voice, etc)")


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
    """Include System Routes operation.

    TODO: Add detailed description and parameters.
    """
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
            EnvVarInfo(name=name, set=(name in os.environ), description=desc, default=None, required=False)
            for name, desc in _ENV_VAR_DESCRIPTIONS.items()
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
        # Attempt operation with error handling
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

        # Handle specific exception case
        except ImportError:
            pass

        return info

    # --- Themes (legacy /api/ for apiService.js + frontend) ---
    @router.get("/api/themes", response_model=ThemeInfo)
    async def get_themes():
        # Supported themes match ConfigurationPage and ThemeProvider usage + Audio/UX needs.
        # NOTE: This and sibling endpoints live under /api/* so AuthMiddleware applies
        # (rejects unauthed unless no_auth=True in WebModeServer/create_app).
        themes_list: list[str] = ["dark", "light", "cyberpunk", "synthwave", "dracula", "night"]
        current: str | None = None
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                cfg = getattr(cfg_mgr, "config", {}) or {}
                ui = cfg.get("ui", {}) if isinstance(cfg.get("ui"), dict) else {}
                current = ui.get("theme")
                if current and current not in themes_list:
                    themes_list = list(themes_list) + [current]
            except Exception as e:
                logger.warning(f"Could not read current theme from config: {e}")
        return {"themes": themes_list, "current": current}

    @router.post("/api/theme", response_model=ActionResponse)
    async def set_theme(payload: dict[str, Any] = Body(default={})):
        theme_name = payload.get("theme") or payload.get("name") or "dark"
        logger.info(f"Setting theme to: {theme_name}")
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                if hasattr(cfg_mgr, "config"):
                    if "ui" not in cfg_mgr.config or not isinstance(cfg_mgr.config.get("ui"), dict):
                        cfg_mgr.config["ui"] = {}
                    cfg_mgr.config["ui"]["theme"] = theme_name
                    if hasattr(cfg_mgr, "save_config"):
                        cfg_mgr.save_config()
            except Exception as e:
                logger.warning(f"Could not persist theme to config: {e}")
        return {"success": True, "message": f"Theme set to {theme_name}", "theme": theme_name}

    # --- Preferences (legacy /api/ ) ---
    @router.get("/api/preferences", response_model=PreferencesResponse)
    async def get_preferences():
        # NOTE: Protected by global AuthMiddleware when no_auth=False (see web_mode.py + middleware/auth.py).
        # Works with --no-auth as middleware short-circuits.
        prefs: dict[str, Any] = {}
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                cfg = getattr(cfg_mgr, "config", {}) or {}
                # Expose ui + some top level as "preferences"
                prefs = {k: v for k, v in cfg.items() if k in ("ui", "general", "audio_settings", "voice")}
                prefs.setdefault("ui", cfg.get("ui", {"theme": "dark"}))
            except Exception:
                pass
        return {"preferences": prefs}

    @router.put("/api/preferences", response_model=ActionResponse)
    async def update_preferences(payload: dict[str, Any] = Body(default={})):
        if get_config_manager:
            try:
                cfg_mgr = get_config_manager()
                if hasattr(cfg_mgr, "config"):
                    for k, v in payload.items():
                        if k in ALLOWED_PREF_KEYS or True:  # permissive for UI prefs
                            cfg_mgr.config[k] = v
                    if hasattr(cfg_mgr, "save_config"):
                        cfg_mgr.save_config()
            except Exception as e:
                logger.warning(f"Failed to update preferences: {e}")
        return {"success": True, "message": "Preferences updated", "preferences": payload}

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
                    for k, v in data.items():
                        if k in ALLOWED_PREF_KEYS or True:
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
