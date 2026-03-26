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

"""OpenAPI endpoint availability and runtime-vs-docs parity tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer, create_app


@pytest.fixture
def client():
    """Create a test client with mocked advisors service."""
    with patch(
        "chatty_commander.web.web_mode.AdvisorsService"
    ) as mock_advisors_service:
        mock_service = MagicMock()
        mock_advisors_service.return_value = mock_service

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


# --- Endpoint availability ---


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


# --- Runtime-vs-docs parity ---


def test_runtime_openapi_matches_docs_file_on_key_paths():
    """
    Parity check: ensure key API paths exist in both runtime schema and docs/openapi.json.
    This is a tolerant check to avoid flakiness when non-key paths change.
    """
    app = create_app(no_auth=True)
    runtime = app.openapi()

    docs_path = Path("docs/openapi.json")
    assert (
        docs_path.is_file()
    ), "docs/openapi.json is missing; generate with make api-docs"
    docs_schema = json.loads(docs_path.read_text(encoding="utf-8"))

    assert "paths" in runtime and isinstance(runtime["paths"], dict)
    assert "paths" in docs_schema and isinstance(docs_schema["paths"], dict)

    runtime_paths = set(runtime["paths"].keys())
    docs_paths = set(docs_schema["paths"].keys())

    # Key endpoints we expect to exist in both
    key = {
        "/api/v1/health",
        "/api/v1/status",
        "/api/v1/config",
        "/api/v1/state",
        "/api/v1/command",
        "/api/v1/version",
    }

    missing_in_runtime = key - runtime_paths
    missing_in_docs = key - docs_paths

    assert (
        not missing_in_runtime
    ), f"Runtime schema missing key paths: {sorted(missing_in_runtime)}"
    assert (
        not missing_in_docs
    ), f"docs/openapi.json missing key paths: {sorted(missing_in_docs)}"
