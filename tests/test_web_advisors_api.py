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
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


class DummyConfig(Config):
    def __init__(self):
        # Provide minimal paths expected by ModelManager
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.auth = {"enabled": True, "api_key": "secret", "allowed_origins": ["*"]}
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
        }


def build_server(cfg, *, no_auth: bool = True):
    with patch(
        "chatty_commander.advisors.providers.build_provider_safe"
    ) as mock_build_provider:
        mock_provider = MagicMock()
        mock_provider.model = "test-model"
        mock_provider.api_mode = "completion"
        mock_build_provider.return_value = mock_provider
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        return WebModeServer(cfg, sm, mm, ce, no_auth=no_auth)


def test_advisors_message_endpoint_echo():
    cfg = DummyConfig()
    server = build_server(cfg)
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
    assert data["reply"] is not None


def test_advisors_message_endpoint_summarize():
    cfg = DummyConfig()
    # Ensure feature flag on
    cfg.advisors["features"] = {"browser_analyst": True}
    server = build_server(cfg)
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
    assert data["reply"] is not None


def test_advisors_message_authentication():
    cfg = DummyConfig()
    server = build_server(cfg, no_auth=False)
    client = TestClient(server.app)

    payload = {
        "platform": "discord",
        "channel": "c1",
        "user": "u1",
        "text": "hello advisors",
    }

    # Missing API key should be unauthorized
    resp = client.post("/api/v1/advisors/message", json=payload)
    assert resp.status_code == 401

    # Providing correct key should succeed
    resp = client.post(
        "/api/v1/advisors/message",
        json=payload,
        headers={"X-API-Key": cfg.auth["api_key"]},
    )
    assert resp.status_code == 200
