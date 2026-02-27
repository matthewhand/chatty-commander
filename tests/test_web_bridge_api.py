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
    def __init__(self, bridge_token: str | None = "test-token") -> None:
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
                    "discord_default": {"system_prompt": "You are a Discord bot."},
                },
                "default_persona": "general",
            },
            "bridge": {},
        }
        # Bridge token - explicitly configured for tests
        self.bridge_token = bridge_token


def build_server(bridge_token: str | None = "test-token"):
    with patch(
        "chatty_commander.advisors.providers.build_provider_safe"
    ) as mock_build_provider:
        mock_provider = MagicMock()
        mock_provider.model = "test-model"
        mock_provider.api_mode = "completion"
        mock_build_provider.return_value = mock_provider
        cfg = DummyConfig(bridge_token=bridge_token)
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        return WebModeServer(cfg, sm, mm, ce, no_auth=True)


def test_bridge_event_returns_503_when_not_configured():
    """When bridge token is not configured, return 503 Service Unavailable."""
    server = build_server(bridge_token=None)
    client = TestClient(server.app)
    resp = client.post("/bridge/event", json={"platform": "discord", "text": "hi"})
    assert resp.status_code == 503


def test_bridge_event_requires_auth():
    """When bridge token is configured but not provided, return 401."""
    server = build_server()
    client = TestClient(server.app)
    resp = client.post("/bridge/event", json={"platform": "discord", "text": "hi"})
    assert resp.status_code == 401


def test_bridge_event_ok_with_valid_token():
    """When valid bridge token is provided, return 200."""
    server = build_server()
    client = TestClient(server.app)
    resp = client.post(
        "/bridge/event",
        headers={"X-Bridge-Token": "test-token"},
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


def test_bridge_event_rejects_invalid_token():
    """When invalid bridge token is provided, return 401."""
    server = build_server()
    client = TestClient(server.app)
    resp = client.post(
        "/bridge/event",
        headers={"X-Bridge-Token": "invalid-token"},
        json={"platform": "discord", "text": "hi"},
    )
    assert resp.status_code == 401
