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

import pytest
from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager

# Import FastAPI app from the source package
from chatty_commander.web.web_mode import WebModeServer


@pytest.fixture
def client():
    """Create a test client with mocked advisors service."""
    with patch(
        "chatty_commander.web.web_mode.AdvisorsService"
    ) as mock_advisors_service:
        # Mock the AdvisorsService to avoid OpenAI API key requirement
        mock_service = MagicMock()
        mock_advisors_service.return_value = mock_service

        # Minimal app factory matching current constructor signatures
        _config = Config()
        _state = StateManager()
        _models = ModelManager(_config)
        _executor = CommandExecutor(_config, _models, _state)
        _server = WebModeServer(
            config_manager=_config,
            state_manager=_state,
            model_manager=_models,
            command_executor=_executor,
            no_auth=True,
        )
        app = _server.app

        return TestClient(app)


def test_swagger_ui_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_openapi_json_available_and_has_paths(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    data = resp.json()
    assert isinstance(data, dict)
    assert "paths" in data and isinstance(data["paths"], dict)
