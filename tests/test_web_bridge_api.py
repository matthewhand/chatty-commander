from unittest.mock import MagicMock, patch

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer
from fastapi.testclient import TestClient


class DummyConfig:
    def __init__(self) -> None:
        # Minimal paths for ModelManager
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {
            "enabled": True,
            "providers": {
                "llm_api_mode": "completion",
                "model": "gpt-oss20b",
            },
            "context": {
                "personas": {
                    "general": {"system_prompt": "You are helpful."},
                    "discord_default": {"system_prompt": "You are a Discord bot."}
                },
                "default_persona": "general"
            },
            "bridge": {"token": "secret", "url": "http://localhost:3001"},
        }


def build_server():
    with patch('chatty_commander.advisors.providers.build_provider_safe') as mock_build_provider:
        mock_provider = MagicMock()
        mock_provider.model = "test-model"
        mock_provider.api_mode = "completion"
        mock_build_provider.return_value = mock_provider
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
    assert data["reply"]["text"] is not None


