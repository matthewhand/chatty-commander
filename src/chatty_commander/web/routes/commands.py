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

from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatty_commander.app.config import Config


class CommandDefinition(BaseModel):
    name: str = Field(..., description="Unique identifier for the command")
    action: str = Field(..., description="Type of action (e.g., keypress, shell, url)")
    description: str | None = Field(None, description="Human-readable description")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Action-specific parameters"
    )


def include_commands_routes(
    get_config_manager: Callable[[], Config],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/commands", response_model=dict[str, Any])
    async def get_commands():
        """Get all configured commands."""
        config = get_config_manager()
        return config.commands

    @router.post("/api/v1/commands")
    async def create_command(command: CommandDefinition):
        """Create or update a command configuration."""
        config = get_config_manager()

        # Construct the command configuration object
        command_config = {"action": command.action}

        # Merge payload into the command config
        if command.payload:
            command_config.update(command.payload)

        # Add description if provided
        if command.description:
            command_config["description"] = command.description

        # Update config
        if not isinstance(config.commands, dict):
            config.commands = {}

        config.commands[command.name] = command_config

        # Save changes
        try:
            config.save_config()
            # Rebuild model actions to make effective immediately
            config.model_actions = config._build_model_actions()
            return {"success": True, "message": f"Command '{command.name}' saved"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

    @router.delete("/api/v1/commands/{command_name}")
    async def delete_command(command_name: str):
        """Delete a command configuration."""
        config = get_config_manager()

        if not isinstance(config.commands, dict) or command_name not in config.commands:
            raise HTTPException(status_code=404, detail=f"Command '{command_name}' not found")

        del config.commands[command_name]

        # Save changes
        try:
            config.save_config()
            # Rebuild model actions to make effective immediately
            config.model_actions = config._build_model_actions()
            return {"success": True, "message": f"Command '{command_name}' deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

    return router
