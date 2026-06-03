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

"""
Comprehensive input validation utilities for API endpoints.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field, validator


class ValidationError(Exception):
    """Custom validation error for better error handling."""

    pass


def validate_uuid(identifier: str, field_name: str = "ID") -> str:
    """
    Validate that a string is a valid UUID.

    Args:
        identifier: The string to validate
        field_name: Name of the field for error messages

    Returns:
        The validated UUID string

    Raises:
        HTTPException: If the identifier is not a valid UUID
    """
    if not identifier:
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")

    try:
        uuid.UUID(identifier)
        return identifier
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name.lower()} format: must be a valid UUID",
        ) from None


def validate_string_length(
    value: str, min_length: int = 1, max_length: int = 1000, field_name: str = "field"
) -> str:
    """
    Validate string length constraints.

    Args:
        value: The string to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages

    Returns:
        The validated string

    Raises:
        HTTPException: If the string doesn't meet length requirements
    """
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a string")

    if len(value) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} characters long",
        )

    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must not exceed {max_length} characters",
        )

    return value.strip()


def validate_agent_name(name: str) -> str:
    """
    Validate agent name with specific constraints.

    Args:
        name: The agent name to validate

    Returns:
        The validated agent name

    Raises:
        HTTPException: If the name is invalid
    """
    name = validate_string_length(
        name, min_length=1, max_length=48, field_name="Agent name"
    )

    # Allow alphanumeric characters, spaces, hyphens, and underscores
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
        raise HTTPException(
            status_code=400,
            detail="Agent name can only contain letters, numbers, spaces, hyphens, and underscores",
        )

    return name


def validate_agent_description(description: str) -> str:
    """
    Validate agent description.

    Args:
        description: The agent description to validate

    Returns:
        The validated description
    """
    return validate_string_length(
        description, min_length=1, max_length=256, field_name="Description"
    )


def validate_persona_prompt(prompt: str) -> str:
    """
    Validate persona prompt with reasonable length limits.

    Args:
        prompt: The persona prompt to validate

    Returns:
        The validated prompt
    """
    return validate_string_length(
        prompt, min_length=10, max_length=5000, field_name="Persona prompt"
    )


def validate_capabilities(capabilities: list[str]) -> list[str]:
    """
    Validate capabilities list.

    Args:
        capabilities: List of capabilities to validate

    Returns:
        The validated capabilities list

    Raises:
        HTTPException: If capabilities are invalid
    """
    if not isinstance(capabilities, list):
        raise HTTPException(status_code=400, detail="Capabilities must be a list")

    if len(capabilities) > 50:
        raise HTTPException(
            status_code=400, detail="Cannot have more than 50 capabilities"
        )

    validated_capabilities = []
    for cap in capabilities:
        if not isinstance(cap, str):
            raise HTTPException(
                status_code=400, detail="Each capability must be a string"
            )

        cap_clean = validate_string_length(
            cap, min_length=1, max_length=100, field_name="Capability"
        )

        # Allow alphanumeric, spaces, and common punctuation
        if not re.match(r"^[a-zA-Z0-9\s\-_,\.]+$", cap_clean):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid capability format: '{cap}'. Only letters, numbers, spaces, hyphens, underscores, commas, and periods are allowed",
            )

        validated_capabilities.append(cap_clean)

    return validated_capabilities


def validate_team_role(role: str | None) -> str | None:
    """
    Validate team role.

    Args:
        role: The team role to validate

    Returns:
        The validated team role or None
    """
    if role is None:
        return None

    role = validate_string_length(
        role, min_length=1, max_length=50, field_name="Team role"
    )

    # Allow alphanumeric, spaces, and common punctuation
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", role):
        raise HTTPException(
            status_code=400,
            detail="Team role can only contain letters, numbers, spaces, hyphens, and underscores",
        )

    return role.lower()


def validate_handoff_triggers(triggers: list[str]) -> list[str]:
    """
    Validate handoff triggers list.

    Args:
        triggers: List of handoff triggers to validate

    Returns:
        The validated triggers list
    """
    if not isinstance(triggers, list):
        raise HTTPException(status_code=400, detail="Handoff triggers must be a list")

    if len(triggers) > 20:
        raise HTTPException(
            status_code=400, detail="Cannot have more than 20 handoff triggers"
        )

    validated_triggers = []
    for trigger in triggers:
        if not isinstance(trigger, str):
            raise HTTPException(
                status_code=400, detail="Each handoff trigger must be a string"
            )

        trigger_clean = validate_string_length(
            trigger, min_length=1, max_length=200, field_name="Handoff trigger"
        )

        validated_triggers.append(trigger_clean)

    return validated_triggers


def validate_command_name(command: str) -> str:
    """
    Validate command name for security.

    Args:
        command: The command name to validate

    Returns:
        The validated command name

    Raises:
        HTTPException: If the command is invalid or potentially dangerous
    """
    command = validate_string_length(
        command, min_length=1, max_length=100, field_name="Command"
    )

    # Prevent command injection attacks
    dangerous_patterns = [
        r"[;&|`$()]",  # Shell metacharacters
        r"\.\./",  # Directory traversal
        r"^\s*rm\s+",  # Dangerous commands
        r"^\s*sudo\s+",  # Privilege escalation
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            raise HTTPException(
                status_code=400,
                detail="Command contains potentially dangerous characters or patterns",
            )

    # Only allow alphanumeric, spaces, hyphens, underscores, and dots
    if not re.match(r"^[a-zA-Z0-9\s\-_\.]+$", command):
        raise HTTPException(
            status_code=400,
            detail="Command can only contain letters, numbers, spaces, hyphens, underscores, and dots",
        )

    return command.strip()


def validate_state_change(state: str) -> str:
    """
    Validate state change value.

    Args:
        state: The state to validate

    Returns:
        The validated state

    Raises:
        HTTPException: If the state is invalid
    """
    valid_states = ["idle", "computer", "chatty"]

    if state not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state. Must be one of: {', '.join(valid_states)}",
        )

    return state


def sanitize_config_data(config_data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize configuration data to prevent injection attacks.

    Args:
        config_data: The configuration data to sanitize

    Returns:
        Sanitized configuration data

    Raises:
        HTTPException: If dangerous content is detected
    """
    if not isinstance(config_data, dict):
        raise HTTPException(
            status_code=400, detail="Configuration data must be a dictionary"
        )

    # Check for potentially dangerous keys
    dangerous_keys = [
        "__proto__",
        "constructor",
        "prototype",
        "eval",
        "function",
        "script",
        "javascript:",
    ]

    for key in config_data.keys():
        if isinstance(key, str):
            key_lower = key.lower()
            if any(dangerous in key_lower for dangerous in dangerous_keys):
                raise HTTPException(
                    status_code=400,
                    detail=f"Configuration contains potentially dangerous key: {key}",
                )

    # Recursively sanitize string values
    def sanitize_value(value: Any) -> Any:
        if isinstance(value, str):
            # Remove potential script injections
            if "<script" in value.lower() or "javascript:" in value.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Configuration contains potentially dangerous script content",
                )
            return value.strip()
        elif isinstance(value, dict):
            return {k: sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [sanitize_value(item) for item in value]
        else:
            return value

    return {k: sanitize_value(v) for k, v in config_data.items()}


# Enhanced Pydantic models with validation
class ValidatedAgentBlueprint(BaseModel):
    """Agent blueprint model with comprehensive validation."""

    name: str = Field(..., description="Agent name", min_length=1, max_length=48)
    description: str = Field(
        ..., description="Agent description", min_length=1, max_length=256
    )
    persona_prompt: str = Field(
        ..., description="Persona prompt", min_length=10, max_length=5000
    )
    capabilities: list[str] = Field(
        default_factory=list, description="List of capabilities"
    )
    team_role: str | None = Field(default=None, description="Team role", max_length=50)
    handoff_triggers: list[str] = Field(
        default_factory=list, description="List of handoff triggers"
    )

    @validator("name")
    def validate_name(cls, v):
        return validate_agent_name(v)

    @validator("description")
    def validate_description(cls, v):
        return validate_agent_description(v)

    @validator("persona_prompt")
    def validate_prompt(cls, v):
        return validate_persona_prompt(v)

    @validator("capabilities")
    def validate_capabilities_list(cls, v):
        return validate_capabilities(v)

    @validator("team_role")
    def validate_role(cls, v):
        return validate_team_role(v)

    @validator("handoff_triggers")
    def validate_triggers(cls, v):
        return validate_handoff_triggers(v)


class ValidatedCommandRequest(BaseModel):
    """Command request model with security validation."""

    command: str = Field(
        ..., description="Command to execute", min_length=1, max_length=100
    )
    parameters: dict[str, Any] | None = Field(
        default=None, description="Optional command parameters"
    )

    @validator("command")
    def validate_command_security(cls, v):
        return validate_command_name(v)


class ValidatedStateChangeRequest(BaseModel):
    """State change request model with validation."""

    state: str = Field(
        ..., description="Target state", pattern="^(idle|computer|chatty)$"
    )

    @validator("state")
    def validate_state_value(cls, v):
        return validate_state_change(v)


class ValidatedConfigUpdate(BaseModel):
    """Configuration update model with sanitization."""

    config_data: dict[str, Any] = Field(..., description="Configuration data to update")

    @validator("config_data")
    def sanitize_config(cls, v):
        return sanitize_config_data(v)
