from __future__ import annotations

import os
import platform
import sys
import time
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field


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

def include_system_routes(
    """Include System Routes operation.

    TODO: Add detailed description and parameters.
    """
    
    *,
    get_start_time: Callable[[], float],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/system/info", response_model=SystemInfo)
    async def get_system_info():
        """Retrieve operation.

        TODO: Add detailed description and parameters.
        """
        
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

    return router
