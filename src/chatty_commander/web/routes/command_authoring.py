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

"""Command authoring routes for LLM-assisted command generation."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from ...llm.manager import LLMManager
except ImportError:
    LLMManager = None  # type: ignore

logger = logging.getLogger(__name__)
router = APIRouter()


class CommandAction(BaseModel):
    """A single action within a command."""

    type: str = Field(
        ...,
        description="Action type: keypress, url, shell, or custom_message",
        pattern="^(keypress|url|shell|custom_message)$",
    )
    keys: str | None = Field(
        default=None,
        description="Keyboard shortcut for keypress actions (e.g., 'ctrl+alt+t')",
    )
    url: str | None = Field(
        default=None,
        description="URL for url actions",
    )
    cmd: str | None = Field(
        default=None,
        description="Shell command for shell actions",
    )
    message: str | None = Field(
        default=None,
        description="Message text for custom_message actions",
    )


class GenerateCommandRequest(BaseModel):
    """Request to generate a command from natural language description."""

    description: str = Field(
        ...,
        description="Natural language description of the desired command behavior",
        min_length=1,
        max_length=2000,
    )


class GeneratedCommandResponse(BaseModel):
    """Response containing a generated command configuration."""

    name: str = Field(
        ...,
        description="Snake_case command identifier",
    )
    display_name: str = Field(
        ...,
        description="Human-readable command name",
    )
    wakeword: str = Field(
        ...,
        description="Voice trigger phrase for the command",
    )
    actions: list[CommandAction] = Field(
        default_factory=list,
        description="Sequence of actions to execute when command is triggered",
    )


# Prompt template for LLM command generation
_COMMAND_GENERATION_PROMPT = """Convert this user request into a command configuration:
"{user_description}"

Available action types:
- keypress: simulate keyboard shortcuts (requires "keys" field referencing keybindings)
- url: HTTP GET request (requires "url" field)
- shell: execute shell command (requires "cmd" field)
- custom_message: display/announce message (requires "message" field)

Output ONLY valid JSON in this format:
{{
  "name": "snake_case_command_name",
  "display_name": "Human Readable Name",
  "wakeword": "voice trigger phrase",
  "actions": [
    {{"type": "action_type", ...action_specific_fields}}
  ]
}}
"""


def _get_llm_manager() -> LLMManager | None:
    """Get or create LLM manager instance."""
    if LLMManager is None:
        return None
    try:
        return LLMManager()
    except Exception as e:
        logger.warning(f"Failed to initialize LLM manager: {e}")
        return None


def _parse_llm_response(response: str) -> dict[str, Any]:
    """Parse and validate LLM response as JSON."""
    # Try to extract JSON from response (handle markdown code blocks)
    cleaned = response.strip()

    # Remove markdown code block markers if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove opening ```json or ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON in LLM response: {e}") from e


def _validate_command_data(data: dict[str, Any]) -> GeneratedCommandResponse:
    """Validate parsed command data against response model."""
    required_fields = {"name", "display_name", "wakeword", "actions"}
    missing = required_fields - set(data.keys())
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate actions
    actions = data.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("'actions' must be a list")

    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ValueError(f"Action {i} must be an object")
        action_type = action.get("type")
        if action_type not in {"keypress", "url", "shell", "custom_message"}:
            raise ValueError(f"Invalid action type '{action_type}' at index {i}")

        # Validate action-specific fields
        if action_type == "keypress" and not action.get("keys"):
            raise ValueError(f"keypress action at index {i} requires 'keys' field")
        if action_type == "url" and not action.get("url"):
            raise ValueError(f"url action at index {i} requires 'url' field")
        if action_type == "shell" and not action.get("cmd"):
            raise ValueError(f"shell action at index {i} requires 'cmd' field")
        if action_type == "custom_message" and not action.get("message"):
            raise ValueError(
                f"custom_message action at index {i} requires 'message' field"
            )

    return GeneratedCommandResponse(**data)


@router.post(
    "/api/v1/commands/generate",
    response_model=GeneratedCommandResponse,
    responses={
        503: {
            "description": "LLM service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "LLM service not available"}
                }
            },
        },
        422: {
            "description": "Invalid LLM response",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid command structure from LLM"}
                }
            },
        },
    },
)
async def generate_command(request: GenerateCommandRequest) -> GeneratedCommandResponse:
    """Generate a command configuration from natural language description.

    Uses LLM to parse the description and generate a structured command
    with appropriate actions. Requires an available LLM backend.

    Args:
        request: Natural language command description

    Returns:
        Generated command configuration with name, display_name, wakeword, and actions

    Raises:
        HTTPException: 503 if LLM unavailable, 422 if response parsing fails
    """
    # Check LLM availability
    llm = _get_llm_manager()
    if llm is None or not llm.is_available():
        raise HTTPException(
            status_code=503,
            detail="LLM service not available. Please configure an LLM backend.",
        )

    # Generate prompt
    prompt = _COMMAND_GENERATION_PROMPT.format(user_description=request.description)

    try:
        # Get LLM response
        response = llm.generate_response(prompt)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"LLM generation failed: {str(e)}",
        ) from e

    # Parse and validate response
    try:
        command_data = _parse_llm_response(response)
        validated_command = _validate_command_data(command_data)
    except ValueError as e:
        logger.error(f"Failed to validate LLM response: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid command structure from LLM: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error processing LLM response: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process LLM response: {str(e)}",
        ) from e

    return validated_command
