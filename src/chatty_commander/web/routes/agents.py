from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


# Placeholder natural language parser (stub for LLM)
def parse_blueprint_from_text(text: str) -> AgentBlueprintModel:
    # Very naive heuristic parser for now
    lines = [l.strip() for l in (text or '').splitlines() if l.strip()]
    name = lines[0][:48] if lines else 'Agent'
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


@router.post('/api/v1/agents/blueprints', response_model=AgentBlueprintResponse)
async def create_blueprint(bp: AgentBlueprintModel | None = None, nl: NLBlueprintRequest | None = None):
    try:
        if nl and nl.description:
            model = parse_blueprint_from_text(nl.description)
        elif bp:
            model = bp
        else:
            raise HTTPException(status_code=400, detail='Provide blueprint or natural language description')
        uid = str(uuid4())
        ent = AgentBlueprint(id=uid, **model.model_dump())
        _STORE[uid] = ent
        if ent.team_role:
            _TEAM.setdefault(ent.team_role, []).append(uid)
        return AgentBlueprintResponse(id=uid, **model.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/api/v1/agents/blueprints', response_model=list[AgentBlueprintResponse])
async def list_blueprints():
    return [AgentBlueprintResponse(id=k, **asdict(v) | {"id": k}) for k, v in _STORE.items()]


@router.put('/api/v1/agents/blueprints/{agent_id}', response_model=AgentBlueprintResponse)
async def update_blueprint(agent_id: str, bp: AgentBlueprintModel):
    if agent_id not in _STORE:
        raise HTTPException(status_code=404, detail='Agent not found')
    ent = AgentBlueprint(id=agent_id, **bp.model_dump())
    _STORE[agent_id] = ent
    return AgentBlueprintResponse(id=agent_id, **bp.model_dump())


@router.delete('/api/v1/agents/blueprints/{agent_id}')
async def delete_blueprint(agent_id: str):
    if agent_id not in _STORE:
        raise HTTPException(status_code=404, detail='Agent not found')
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


@router.get('/api/v1/agents/team', response_model=TeamInfo)
async def get_team():
    agents = [AgentBlueprintResponse(id=k, **asdict(v) | {"id": k}) for k, v in _STORE.items()]
    return TeamInfo(roles={k: list(v) for k, v in _TEAM.items()}, agents=agents)


class HandoffRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    reason: str | None = None


@router.post('/api/v1/agents/team/handoff')
async def handoff(h: HandoffRequest):
    if h.from_agent_id not in _STORE or h.to_agent_id not in _STORE:
        raise HTTPException(status_code=404, detail='Agent not found')
    # For now, just acknowledge; future: integrate with thinking_state + avatar_ws
    return {"ok": True, "from": h.from_agent_id, "to": h.to_agent_id, "reason": h.reason}
