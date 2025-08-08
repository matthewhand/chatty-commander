from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import WebModeServer
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.command_executor import CommandExecutor


class DummyConfig(Config):
    def __init__(self):
        # Provide minimal paths expected by ModelManager
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {
            "enabled": True,
            "llm_api_mode": "completion",
            "model": "gpt-oss20b",
        }


def test_advisors_message_endpoint_echo():
    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    resp = client.post(
        "/api/v1/advisors/message",
        json={
            "platform": "discord",
            "channel": "c1",
            "user": "u1",
            "text": "hello advisors",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "advisor:gpt-oss20b/completion" in data["text"]
    assert "hello advisors" in data["text"]


def test_advisors_message_endpoint_summarize():
    cfg = DummyConfig()
    # Ensure feature flag on
    cfg.advisors["features"] = {"browser_analyst": True}
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    resp = client.post(
        "/api/v1/advisors/message",
        json={
            "platform": "discord",
            "channel": "c1",
            "user": "u1",
            "text": "summarize https://example.com/x",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["url"].endswith("/x")
    # Persona tag is optional; if default, it may be omitted


