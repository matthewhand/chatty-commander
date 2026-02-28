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

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

try:
    from chatty_commander.llm.manager import LLMManager as _LLMManager
except ImportError:
    _LLMManager = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Module-level singleton to avoid creating a new LLMManager on every request
_llm_manager: Any = None


def _get_llm_manager() -> Any:
    """Return a cached LLMManager instance, or None if unavailable."""
    global _llm_manager
    if _llm_manager is None and _LLMManager is not None:
        try:
            _llm_manager = _LLMManager()
        except Exception as exc:
            logger.debug("LLMManager init failed: %s", exc)
    return _llm_manager


router = APIRouter()


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
    name: str = Field(...)
    description: str = Field(...)
    persona_prompt: str = Field(...)
    capabilities: list[str] = Field(default_factory=list)
    team_role: str | None = Field(default=None)
    handoff_triggers: list[str] = Field(default_factory=list)


class AgentBlueprintResponse(AgentBlueprintModel):
    id: str


# In-memory store (replace with persistence later)
_STORE: dict[str, AgentBlueprint] = {}
_TEAM: dict[str, list[str]] = {}  # role -> [agent_ids]


def _extract_json_from_response(response: str) -> str:
    """Extract JSON content from a response that may contain markdown code blocks."""
    # Use regex to safely extract content between ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
    if match:
        return match.group(1).strip()
    return response.strip()


def parse_blueprint_from_text(text: str) -> AgentBlueprintModel:
    llm = _get_llm_manager()
    if llm is not None and llm.is_available():
        try:
            prompt = f"""
Extract an agent blueprint from the following text.
Return a JSON object with EXACTLY these keys:
- "name" (string, short)
- "description" (string, short summary)
- "persona_prompt" (string, detailed prompt)
- "capabilities" (list of strings, inferred abilities)
- "team_role" (string or null, inferred role if any)

Text:
{text}

Return ONLY valid JSON.
"""
            response = llm.generate_response(prompt)
            # Safely extract JSON from possible markdown code block
            json_str = _extract_json_from_response(response)
            data = json.loads(json_str)
            return AgentBlueprintModel(
                name=data.get("name", "Agent")[:48],
                description=data.get("description", text.strip()[:256]),
                persona_prompt=data.get("persona_prompt", text.strip()),
                capabilities=data.get("capabilities", []),
                team_role=data.get("team_role"),
                handoff_triggers=[],
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.debug("LLM blueprint parsing failed, using heuristic fallback: %s", exc)

    # Very naive heuristic parser fallback
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
        # If a simple NL description payload
        if (
            isinstance(payload, dict)
            and "description" in payload
            and len(payload.keys()) == 1
        ):
            model = parse_blueprint_from_text(str(payload.get("description", "")))
        else:
            # Try to parse as structured blueprint
            model = AgentBlueprintModel(**payload)
        uid = str(uuid4())
        ent = AgentBlueprint(id=uid, **model.model_dump())
        _STORE[uid] = ent
        if ent.team_role:
            _TEAM.setdefault(ent.team_role, []).append(uid)
        return AgentBlueprintResponse(id=uid, **model.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/v1/agents/blueprints", response_model=list[AgentBlueprintResponse])
async def list_blueprints():
    # Each AgentBlueprint already contains its id; avoid passing 'id' twice
    return [AgentBlueprintResponse(**asdict(v)) for v in _STORE.values()]


@router.put(
    "/api/v1/agents/blueprints/{agent_id}", response_model=AgentBlueprintResponse
)
async def update_blueprint(agent_id: str, bp: AgentBlueprintModel):
    if agent_id not in _STORE:
        raise HTTPException(status_code=404, detail="Agent not found")
    ent = AgentBlueprint(id=agent_id, **bp.model_dump())
    _STORE[agent_id] = ent
    return AgentBlueprintResponse(id=agent_id, **bp.model_dump())


@router.delete("/api/v1/agents/blueprints/{agent_id}")
async def delete_blueprint(agent_id: str):
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
    if h.from_agent_id not in _STORE or h.to_agent_id not in _STORE:
        raise HTTPException(status_code=404, detail="Agent not found")
    # For now, just acknowledge; future: integrate with thinking_state + avatar_ws
    return {
        "ok": True,
        "from": h.from_agent_id,
        "to": h.to_agent_id,
        "reason": h.reason,
    }
