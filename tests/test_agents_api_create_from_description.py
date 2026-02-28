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

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


class DummyConfig:
    def __init__(self) -> None:
        # Minimal paths and actions for ModelManager/Executor
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


@patch("chatty_commander.web.routes.agents.LLMManager")
def test_create_agent_blueprint_from_description(mock_llm_manager_class):
    # Test fallback directly when LLM is unavailable
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = False
    mock_llm_manager_class.return_value = mock_llm

    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["name"] == "My helpful agent who summarizes docs"
    assert data["persona_prompt"] == "My helpful agent who summarizes docs"


@patch("chatty_commander.web.routes.agents.LLMManager")
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

    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

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


@patch("chatty_commander.web.routes.agents.LLMManager")
def test_create_agent_blueprint_from_description_llm_fallback(mock_llm_manager_class):
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    # Return invalid json
    mock_llm.generate_response.return_value = "This is not JSON at all."
    mock_llm_manager_class.return_value = mock_llm

    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    # Should fall back to naive parsing
    assert data["name"] == "My helpful agent who summarizes docs"
    assert data["persona_prompt"] == "My helpful agent who summarizes docs"
