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

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# Validation functions
def validate_uuid_field(identifier: str, field_name: str = "ID") -> str:
    """Validate that a string is a valid UUID."""
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


def validate_string_field(
    value: str, min_length: int = 1, max_length: int = 1000, field_name: str = "field"
) -> str:
    """Validate string length constraints."""
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


def validate_agent_name_field(name: str) -> str:
    """Validate agent name with specific constraints."""
    name = validate_string_field(
        name, min_length=1, max_length=48, field_name="Agent name"
    )

    # Allow alphanumeric characters, spaces, hyphens, and underscores
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
        raise HTTPException(
            status_code=400,
            detail="Agent name can only contain letters, numbers, spaces, hyphens, and underscores",
        )

    return name


def validate_capabilities_field(capabilities: list[str]) -> list[str]:
    """Validate capabilities list."""
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

        cap_clean = validate_string_field(
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


@dataclass
class AgentBlueprint:
    id: str
    name: str
    description: str
    persona_prompt: str
    capabilities: list[str] = field(default_factory=list)
    team_role: str | None = None
    handoff_triggers: list[str] = field(default_factory=list)


class AgentBlueprintModel(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    persona_prompt: str = Field(..., description="Persona prompt")
    capabilities: list[str] = Field(
        default_factory=list, description="List of capabilities"
    )
    team_role: str | None = Field(default=None, description="Team role")
    handoff_triggers: list[str] = Field(
        default_factory=list, description="List of handoff triggers"
    )


class AgentBlueprintResponse(AgentBlueprintModel):
    id: str


# In-memory store (replace with persistence later)
_STORE: dict[str, AgentBlueprint] = {}
_TEAM: dict[str, list[str]] = {}  # role -> [agent_ids]


# Placeholder natural language parser (stub for LLM)
def parse_blueprint_from_text(text: str) -> AgentBlueprintModel:
    # Very naive heuristic parser for now
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    name = lines[0][:48] if lines else "Agent"
    description = text.strip()[:256]
    persona_prompt = text.strip()
    return AgentBlueprintModel(
        name=name,
        description=description,
        persona_prompt=persona_prompt,
        capabilities=[],
        team_role=None,
        handoff_triggers=[],
    )


class NLBlueprintRequest(BaseModel):
    description: str


@router.post("/api/v1/agents/blueprints", response_model=AgentBlueprintResponse)
async def create_blueprint(
    payload: Annotated[dict[str, Any], Body(...)],
) -> AgentBlueprintResponse:
    try:
        # Validate payload structure
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Payload must be a dictionary")

        # If a simple NL description payload
        if "description" in payload and len(payload.keys()) == 1:
            description = str(payload.get("description", ""))
            if not description.strip():
                raise HTTPException(
                    status_code=400, detail="Description cannot be empty"
                )

            model = parse_blueprint_from_text(description)
            # Validate the parsed model
            model.name = validate_agent_name_field(model.name)
            model.description = validate_string_field(
                model.description,
                min_length=1,
                max_length=256,
                field_name="Description",
            )
            model.persona_prompt = validate_string_field(
                model.persona_prompt,
                min_length=10,
                max_length=5000,
                field_name="Persona prompt",
            )
            model.capabilities = validate_capabilities_field(model.capabilities)
        else:
            # Try to parse as structured blueprint with validation
            model = AgentBlueprintModel(**payload)
            # Validate individual fields
            model.name = validate_agent_name_field(model.name)
            model.description = validate_string_field(
                model.description,
                min_length=1,
                max_length=256,
                field_name="Description",
            )
            model.persona_prompt = validate_string_field(
                model.persona_prompt,
                min_length=10,
                max_length=5000,
                field_name="Persona prompt",
            )
            model.capabilities = validate_capabilities_field(model.capabilities)

            if model.team_role is not None:
                model.team_role = validate_string_field(
                    model.team_role, min_length=1, max_length=50, field_name="Team role"
                )
                if not re.match(r"^[a-zA-Z0-9\s\-_]+$", model.team_role):
                    raise HTTPException(
                        status_code=400,
                        detail="Team role can only contain letters, numbers, spaces, hyphens, and underscores",
                    )
                model.team_role = model.team_role.lower()

        uid = str(uuid4())
        ent = AgentBlueprint(id=uid, **model.model_dump())
        _STORE[uid] = ent
        if ent.team_role:
            _TEAM.setdefault(ent.team_role, []).append(uid)
        return AgentBlueprintResponse(id=uid, **model.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from e


@router.get("/api/v1/agents/blueprints", response_model=list[AgentBlueprintResponse])
async def list_blueprints():
    # Each AgentBlueprint already contains its id; avoid passing 'id' twice
    return [AgentBlueprintResponse(**asdict(v)) for v in _STORE.values()]


@router.put(
    "/api/v1/agents/blueprints/{agent_id}", response_model=AgentBlueprintResponse
)
async def update_blueprint(agent_id: str, bp: AgentBlueprintModel):
    # Validate agent_id
    validate_uuid_field(agent_id, "Agent ID")

    if agent_id not in _STORE:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate blueprint data
    bp.name = validate_agent_name_field(bp.name)
    bp.description = validate_string_field(
        bp.description, min_length=1, max_length=256, field_name="Description"
    )
    bp.persona_prompt = validate_string_field(
        bp.persona_prompt, min_length=10, max_length=5000, field_name="Persona prompt"
    )
    bp.capabilities = validate_capabilities_field(bp.capabilities)

    if bp.team_role is not None:
        bp.team_role = validate_string_field(
            bp.team_role, min_length=1, max_length=50, field_name="Team role"
        )
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", bp.team_role):
            raise HTTPException(
                status_code=400,
                detail="Team role can only contain letters, numbers, spaces, hyphens, and underscores",
            )
        bp.team_role = bp.team_role.lower()

    ent = AgentBlueprint(id=agent_id, **bp.model_dump())
    _STORE[agent_id] = ent
    return AgentBlueprintResponse(id=agent_id, **bp.model_dump())


@router.delete("/api/v1/agents/blueprints/{agent_id}")
async def delete_blueprint(agent_id: str):
    # Validate agent_id
    validate_uuid_field(agent_id, "Agent ID")

    if agent_id not in _STORE:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Safety: ensure not in active team relations (simplified)
    for role, ids in list(_TEAM.items()):
        if agent_id in ids:
            ids.remove(agent_id)
            if not ids:
                _TEAM.pop(role, None)
    _STORE.pop(agent_id, None)
    return {"deleted": True, "id": agent_id}


class TeamInfo(BaseModel):
    roles: dict[str, list[str]] = Field(default_factory=dict)
    agents: list[AgentBlueprintResponse] = Field(default_factory=list)


@router.get("/api/v1/agents/team", response_model=TeamInfo)
async def get_team():
    agents = [AgentBlueprintResponse(**asdict(v)) for v in _STORE.values()]
    return TeamInfo(roles={k: list(v) for k, v in _TEAM.items()}, agents=agents)


class HandoffRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    reason: str | None = None


@router.post("/api/v1/agents/team/handoff")
async def handoff(h: HandoffRequest):
    # Validate agent IDs
    validate_uuid_field(h.from_agent_id, "From agent ID")
    validate_uuid_field(h.to_agent_id, "To agent ID")

    if h.from_agent_id not in _STORE or h.to_agent_id not in _STORE:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate reason if provided
    if h.reason is not None:
        h.reason = validate_string_field(
            h.reason, min_length=1, max_length=500, field_name="Handoff reason"
        )

    # For now, just acknowledge; future: integrate with thinking_state + avatar_ws
    return {
        "ok": True,
        "from": h.from_agent_id,
        "to": h.to_agent_id,
        "reason": h.reason,
    }
