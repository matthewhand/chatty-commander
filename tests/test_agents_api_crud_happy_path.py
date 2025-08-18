from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.routes.agents import AgentBlueprintModel
from chatty_commander.web.web_mode import WebModeServer


class DummyConfig:
    def __init__(self) -> None:
        # Minimal paths and actions for ModelManager/Executor
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


def test_agents_crud_happy_path_isolated_store():
    # Isolate store
    try:
        from chatty_commander.web.routes import agents as _agents_mod

        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass

    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    payload = AgentBlueprintModel(
        name="A1",
        description="desc",
        persona_prompt="prompt",
        capabilities=["x"],
    ).model_dump()

    # Create
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    created = r.json()
    uid = created["id"]

    # List
    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == uid for i in items)

    # Update
    payload["name"] = "A1-Updated"
    r = client.put(f"/api/v1/agents/blueprints/{uid}", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "A1-Updated"

    # Delete
    r = client.delete(f"/api/v1/agents/blueprints/{uid}")
    assert r.status_code == 200

    # List empty again
    r = client.get("/api/v1/agents/blueprints")
    assert all(i["id"] != uid for i in r.json())
