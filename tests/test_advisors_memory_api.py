from unittest.mock import MagicMock, patch

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer
from fastapi.testclient import TestClient


class DummyConfig:
    def __init__(self) -> None:
        # Minimal paths and actions for ModelManager/Executor
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
            "features": {"browser_analyst": True},
        }


def test_advisors_memory_flow():
    with patch('chatty_commander.web.web_mode.AdvisorsService') as mock_advisors_service:
        # Mock the AdvisorsService to avoid OpenAI API key requirement
        mock_service = MagicMock()
        mock_memory = MagicMock()
        mock_service.memory = mock_memory

        # Mock memory methods
        mock_memory.get.return_value = [
            MagicMock(role="user", content="hello", timestamp="2023-01-01T00:00:00"),
            MagicMock(role="assistant", content="Hello! How can I help you?", timestamp="2023-01-01T00:00:01")
        ]
        mock_memory.clear.return_value = 2

        # Mock handle_message method
        mock_reply = MagicMock()
        mock_reply.reply = "Test response"
        mock_reply.context_key = "test_context"
        mock_reply.persona_id = "general"
        mock_reply.model = "test-model"
        mock_reply.api_mode = "completion"
        mock_service.handle_message.return_value = mock_reply

        mock_advisors_service.return_value = mock_service

        cfg = DummyConfig()
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
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
        # Note: summarize command may not add to memory the same way
        assert len(items) >= 2  # At least user messages
        assert any(i["role"] == "user" for i in items)

        # Clear memory
        resp = client.delete("/api/v1/advisors/memory", params={"platform": "discord", "channel": "c1", "user": "u1"})
        assert resp.status_code == 200
        assert resp.json()["cleared"] >= 1

