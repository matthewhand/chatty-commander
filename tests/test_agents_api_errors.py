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


def test_create_blueprint_invalid_payload_returns_400():
    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)
    # Missing required fields for AgentBlueprintModel; payload will fail validation in route
    r = client.post("/api/v1/agents/blueprints", json={"name": 123})
    assert r.status_code == 400
