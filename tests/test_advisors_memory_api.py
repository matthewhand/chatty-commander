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
            "features": {"browser_analyst": True},
        }


def build_server():
    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    return WebModeServer(cfg, sm, mm, ce, no_auth=True)


def test_advisors_memory_flow():
    server = build_server()
    client = TestClient(server.app)

    # Send two messages
    client.post(
        "/api/v1/advisors/message",
        json={
            "platform": "discord",
            "channel": "c1",
            "user": "u1",
            "text": "hello",
        },
    )
    client.post(
        "/api/v1/advisors/message",
        json={
            "platform": "discord",
            "channel": "c1",
            "user": "u1",
            "text": "summarize https://example.com/x",
        },
    )

    # Read memory
    resp = client.get("/api/v1/advisors/memory", params={"platform": "discord", "channel": "c1", "user": "u1"})
    assert resp.status_code == 200
    items = resp.json()
    # Expect 4 items: user+assistant for each message
    assert len(items) == 4
    assert any(i["role"] == "assistant" for i in items)

    # Clear memory
    resp = client.delete("/api/v1/advisors/memory", params={"platform": "discord", "channel": "c1", "user": "u1"})
    assert resp.status_code == 200
    assert resp.json()["cleared"] >= 1

