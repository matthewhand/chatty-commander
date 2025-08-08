from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import WebModeServer
from chatty_commander.app.state_manager import StateManager
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.command_executor import CommandExecutor


class DummyConfig:
    def __init__(self) -> None:
        self.config = {}
        self.advisors = {
            "enabled": True,
            "llm_api_mode": "completion",
            "model": "gpt-oss20b",
            "bridge": {"token": "secret", "url": "http://localhost:3001"},
        }


def build_server():
    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    return WebModeServer(cfg, sm, mm, ce, no_auth=True)


def test_bridge_event_requires_auth():
    server = build_server()
    client = TestClient(server.app)
    resp = client.post("/bridge/event", json={"platform": "discord", "text": "hi"})
    assert resp.status_code == 401


def test_bridge_event_ok_with_secret():
    server = build_server()
    client = TestClient(server.app)
    resp = client.post(
        "/bridge/event",
        headers={"X-Bridge-Token": "secret"},
        json={
            "platform": "discord",
            "channel": "c1",
            "user": "u1",
            "text": "hello via bridge",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "advisor:gpt-oss20b/completion" in data["reply"]["text"]


