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

"""Consolidated agents API tests: CRUD, errors, team/handoff, persistence, create-from-description."""

import importlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.routes import agents as _agents_mod
from chatty_commander.web.routes.agents import AgentBlueprint, AgentBlueprintModel
from chatty_commander.web.server import create_app
from chatty_commander.web.web_mode import WebModeServer


@pytest.fixture(autouse=True)
def _clear_agent_store():
    """Reset global agent store and team state before every test."""
    _agents_mod._STORE.clear()
    _agents_mod._TEAM.clear()
    yield
    _agents_mod._STORE.clear()
    _agents_mod._TEAM.clear()


@pytest.fixture()
def client():
    """Provide a TestClient backed by a no-auth app."""
    app = create_app(no_auth=True)
    return TestClient(app)


def _blueprint_payload(**overrides):
    """Return a valid AgentBlueprintModel dict, with optional overrides."""
    defaults = {
        "name": "TestAgent",
        "description": "A test agent",
        "persona_prompt": "You are a test agent",
        "capabilities": ["test"],
    }
    defaults.update(overrides)
    return AgentBlueprintModel(**defaults).model_dump()


# ── List ─────────────────────────────────────────────────────────────────


def test_list_blueprints_initially_empty(client):
    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    assert r.json() == []


# ── CRUD happy path ──────────────────────────────────────────────────────


def test_crud_happy_path(client):
    payload = _blueprint_payload(name="A1")

    # Create
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    uid = r.json()["id"]

    # List
    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    assert any(i["id"] == uid for i in r.json())

    # Update
    payload["name"] = "A1-Updated"
    r = client.put(f"/api/v1/agents/blueprints/{uid}", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "A1-Updated"

    # Delete
    r = client.delete(f"/api/v1/agents/blueprints/{uid}")
    assert r.status_code == 200

    # Confirm deleted
    r = client.get("/api/v1/agents/blueprints")
    assert all(i["id"] != uid for i in r.json())


# ── Error cases ──────────────────────────────────────────────────────────


def test_create_blueprint_invalid_payload_returns_400(client):
    r = client.post("/api/v1/agents/blueprints", json={"name": 123})
    assert r.status_code == 400


def test_update_blueprint_nonexistent_returns_404(client):
    payload = _blueprint_payload(
        name="X", description="Y", persona_prompt="Z", capabilities=[]
    )
    r = client.put("/api/v1/agents/blueprints/does-not-exist", json=payload)
    assert r.status_code == 404


def test_delete_blueprint_nonexistent_returns_404(client):
    r = client.delete("/api/v1/agents/blueprints/does-not-exist")
    assert r.status_code == 404


# ── Team / handoff ───────────────────────────────────────────────────────


def test_handoff_between_missing_agents_returns_404(client):
    r = client.post(
        "/api/v1/agents/team/handoff",
        json={"from_agent_id": "a", "to_agent_id": "b", "reason": "test"},
    )
    assert r.status_code == 404


def test_team_info_and_handoff(client):
    # Create two agents
    p1 = _blueprint_payload(name="Analyst", capabilities=["summarize", "route"])
    r1 = client.post("/api/v1/agents/blueprints", json=p1)
    assert r1.status_code == 200
    aid = r1.json()["id"]

    # Update with team_role / handoff_triggers
    p1.update({"team_role": "analyst", "handoff_triggers": ["needs_coding"]})
    r = client.put(f"/api/v1/agents/blueprints/{aid}", json=p1)
    assert r.status_code == 200

    p2 = _blueprint_payload(name="Coder", description="Implements tasks")
    r2 = client.post("/api/v1/agents/blueprints", json=p2)
    assert r2.status_code == 200
    bid = r2.json()["id"]

    # Team info
    r = client.get("/api/v1/agents/team")
    assert r.status_code == 200
    data = r.json()
    assert "roles" in data and "agents" in data

    # Handoff
    r = client.post(
        "/api/v1/agents/team/handoff",
        json={"from_agent_id": aid, "to_agent_id": bid, "reason": "needs_coding"},
    )
    assert r.status_code == 200


# ── Persistence ──────────────────────────────────────────────────────────


def test_agent_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "agents.json"

        with patch.dict(os.environ, {"CHATTY_AGENTS_STORE": str(store_path)}):
            importlib.reload(_agents_mod)

            _agents_mod._STORE.clear()
            _agents_mod._TEAM.clear()

            assert not store_path.exists()

            bp = AgentBlueprintModel(
                name="TestAgent",
                description="Test description",
                persona_prompt="You are a test agent.",
                capabilities=["test"],
                team_role="tester",
            )

            uid = str(uuid4())
            ent = AgentBlueprint(id=uid, **bp.model_dump())
            _agents_mod._STORE[uid] = ent
            if ent.team_role:
                _agents_mod._TEAM.setdefault(ent.team_role, []).append(uid)
            _agents_mod._save_store()

            assert store_path.exists()
            with store_path.open("r", encoding="utf-8") as f:
                saved_data = json.load(f)
                assert "agents" in saved_data
                assert len(saved_data["agents"]) == 1
                assert saved_data["agents"][0]["name"] == "TestAgent"

            _agents_mod._STORE.clear()
            _agents_mod._TEAM.clear()
            assert len(_agents_mod._STORE) == 0

            importlib.reload(_agents_mod)

            assert len(_agents_mod._STORE) == 1
            assert uid in _agents_mod._STORE
            loaded_ent = _agents_mod._STORE[uid]
            assert loaded_ent.name == "TestAgent"
            assert loaded_ent.team_role == "tester"
            assert "tester" in _agents_mod._TEAM
            assert uid in _agents_mod._TEAM["tester"]


# ── Create from description ──────────────────────────────────────────────


class _DummyConfig:
    def __init__(self) -> None:
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


def _description_client():
    """Build a TestClient with full WebModeServer for description tests."""
    from chatty_commander.app import CommandExecutor

    cfg = _DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    return TestClient(server.app)


@patch("chatty_commander.web.routes.agents._llm_manager", None)
@patch("chatty_commander.web.routes.agents._LLMManager")
def test_create_agent_blueprint_from_description(mock_llm_manager_class):
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = False
    mock_llm_manager_class.return_value = mock_llm

    client = _description_client()
    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["name"] == "My helpful agent who summarizes docs"
    assert data["persona_prompt"] == "My helpful agent who summarizes docs"


@patch("chatty_commander.web.routes.agents._llm_manager", None)
@patch("chatty_commander.web.routes.agents._LLMManager")
def test_create_agent_blueprint_from_description_llm_success(mock_llm_manager_class):
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True

    mock_json_response = """```json
    {
        "name": "Doc Summarizer",
        "description": "An expert at summarizing technical documentation.",
        "persona_prompt": "You are Doc Summarizer. You summarize docs.",
        "capabilities": ["summarize", "read_files"],
        "team_role": "summarizer"
    }
    ```"""
    mock_llm.generate_response.return_value = mock_json_response
    mock_llm_manager_class.return_value = mock_llm

    client = _description_client()
    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["name"] == "Doc Summarizer"
    assert data["description"] == "An expert at summarizing technical documentation."
    assert data["persona_prompt"] == "You are Doc Summarizer. You summarize docs."
    assert data["capabilities"] == ["summarize", "read_files"]
    assert data["team_role"] == "summarizer"


@patch("chatty_commander.web.routes.agents._llm_manager", None)
@patch("chatty_commander.web.routes.agents._LLMManager")
def test_create_agent_blueprint_from_description_llm_fallback(mock_llm_manager_class):
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.generate_response.return_value = "This is not JSON at all."
    mock_llm_manager_class.return_value = mock_llm

    client = _description_client()
    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["name"] == "My helpful agent who summarizes docs"
    assert data["persona_prompt"] == "My helpful agent who summarizes docs"
