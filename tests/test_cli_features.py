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

"""Consolidated CLI tests: dispatch modes, list/exec features."""

import io
import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# Patch sys.modules to mock openwakeword for imports
sys.modules["openwakeword"] = types.ModuleType("openwakeword")
_mock_model_mod = types.ModuleType("openwakeword.model")
_mock_model_mod.Model = type("Model", (), {})
sys.modules["openwakeword.model"] = _mock_model_mod

from chatty_commander.cli.cli import cli_main  # noqa: E402

# ── Helpers / fixtures ───────────────────────────────────────────────────


class DummyConfigDirect:
    def __init__(self, actions):
        self.model_actions = actions
        self.general_models_path = {}
        self.system_models_path = {}
        self.chat_models_path = {}


@pytest.fixture
def replace_config_with_dummy(monkeypatch):
    def _factory(actions):
        import chatty_commander.app.config as config_module
        from chatty_commander.cli import cli as cli_module

        monkeypatch.setattr(
            config_module, "Config", staticmethod(lambda: DummyConfigDirect(actions))
        )
        monkeypatch.setattr(cli_module, "Config", lambda: DummyConfigDirect(actions))

        class DummyModelManager:
            def __init__(self, config, mock_models=False):
                self.config = config
                self.models = {"general": {}, "system": {}, "chat": {}}
                self.active_models = {}

            def reload_models(self, *args, **kwargs):
                pass

            def get_model(self, name):
                return None

            def set_state(self, state):
                pass

        monkeypatch.setattr(cli_module, "ModelManager", DummyModelManager)

        class DummyStateManager:
            def __init__(self):
                self.state = "idle"
                self.current_state = "idle"

            def get_state(self):
                return self.state

            def set_state(self, state):
                self.state = state
                self.current_state = state

        monkeypatch.setattr(cli_module, "StateManager", DummyStateManager)

        return lambda: DummyConfigDirect(actions)

    return _factory


def _run_cli_main_with_args(args_list, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["chatty-commander"] + args_list)
    stdout = io.StringIO()
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    try:
        cli_main()
        code = 0
    except SystemExit as e:
        code = int(e.code) if e.code is not None else 0
    return code, stdout.getvalue(), stderr.getvalue()


# ── CLI dispatch modes (from test_cli_integration) ───────────────────────


class TestCLIDispatch:
    """Tests for cli_main() dispatch: help, web, gui, config, shell."""

    def test_cli_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["chatty-commander", "--help"])
        ret = cli_main()
        assert ret == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "usage:" in captured.err
        assert "ChattyCommander" in captured.out

    def test_cli_web_mode(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["chatty-commander", "--web", "--no-auth"])
        with patch("chatty_commander.cli.cli.run_web_mode") as mock_web:
            cli_main()
            mock_web.assert_called_once()
            _args, kwargs = mock_web.call_args
            assert kwargs.get("no_auth") is True

    def test_cli_gui_mode(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["chatty-commander", "--gui", "--no-gui"])
        with patch("chatty_commander.cli.cli.run_gui_mode") as mock_gui:
            cli_main()
            mock_gui.assert_called_once()
            _args, kwargs = mock_gui.call_args
            assert kwargs.get("no_gui") is True

    def test_cli_config_wizard(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["chatty-commander", "--config"])
        mock_config_cli_cls = MagicMock()
        mock_instance = mock_config_cli_cls.return_value
        with patch.dict(
            sys.modules,
            {"chatty_commander.config_cli": MagicMock(ConfigCLI=mock_config_cli_cls)},
        ):
            cli_main()
            mock_config_cli_cls.assert_called()
            mock_instance.run_wizard.assert_called_once()

    def test_cli_interactive_shell(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["chatty-commander"])
        with patch("chatty_commander.cli.cli.run_interactive_shell") as mock_shell:
            cli_main()
            mock_shell.assert_called_once()


# ── List / exec features ────────────────────────────────────────────────


class TestCLIListExec:
    """Tests for CLI list and exec sub-commands."""

    def test_list_text(self, monkeypatch, replace_config_with_dummy):
        actions = {
            "hello": {"shell": {"cmd": "echo hello"}},
            "web": {"url": {"url": "https://example.com"}},
        }
        replace_config_with_dummy(actions)
        code, out, err = _run_cli_main_with_args(["list"], monkeypatch)
        assert code == 0
        lines = [ln.rstrip() for ln in out.strip().splitlines()]
        assert lines[0] == "Available commands:"
        assert "- hello" in lines
        assert "- web" in lines
        assert err == ""

    def test_list_json(self, monkeypatch, replace_config_with_dummy):
        actions = {
            "cmd1": {"shell": {"cmd": "true"}},
            "cmd2": {"url": {"url": "https://x"}},
        }
        replace_config_with_dummy(actions)
        code, out, err = _run_cli_main_with_args(["list", "--json"], monkeypatch)
        assert code == 0
        data = json.loads(out.strip())
        names = {d["name"] for d in data}
        types_ = {d["type"] for d in data}
        assert names == {"cmd1", "cmd2"}
        assert "shell" in types_ and "url" in types_
        assert err == ""

    def test_list_empty_config(self, monkeypatch, replace_config_with_dummy):
        replace_config_with_dummy({})
        code, out, err = _run_cli_main_with_args(["list"], monkeypatch)
        assert code == 0
        assert out.strip() == "No commands configured."
        assert err == ""

    def test_exec_unknown_command(self, monkeypatch, replace_config_with_dummy):
        replace_config_with_dummy({"known": {"shell": {"cmd": "echo ok"}}})
        code, out, err = _run_cli_main_with_args(["exec", "missing"], monkeypatch)
        assert code == 1
        assert out == ""
        assert "Unknown command: missing" in err

    def test_exec_dry_run(self, monkeypatch, replace_config_with_dummy):
        actions = {"hello": {"shell": {"cmd": "echo hi"}}}
        replace_config_with_dummy(actions)
        code, out, err = _run_cli_main_with_args(
            ["exec", "hello", "--dry-run"], monkeypatch
        )
        assert code == 0
        assert "DRY RUN: would execute command 'hello'" in out
        assert err == ""

    def test_exec_invokes_executor(self, monkeypatch, replace_config_with_dummy):
        actions = {"hello": {"shell": {"cmd": "echo hi"}}}
        replace_config_with_dummy(actions)

        called = {"count": 0, "last": None}

        class FakeExecutor:
            def __init__(self, cfg, a, b):
                self.cfg = cfg

            def execute_command(self, name):
                called["count"] += 1
                called["last"] = name

        monkeypatch.setattr("chatty_commander.cli.cli.CommandExecutor", FakeExecutor)

        code, out, err = _run_cli_main_with_args(["exec", "hello"], monkeypatch)
        assert code == 0
        assert called["count"] == 1
        assert called["last"] == "hello"
        assert err == ""

    def test_exec_timeout_flag(self, monkeypatch, replace_config_with_dummy):
        actions = {"hello": {"shell": {"cmd": "sleep 0"}}}
        replace_config_with_dummy(actions)

        class NoopExecutor:
            def __init__(self, cfg, a, b):
                pass

            def execute_command(self, name):
                return

        monkeypatch.setattr(
            "chatty_commander.app.command_executor.CommandExecutor", NoopExecutor
        )

        code, out, err = _run_cli_main_with_args(
            ["exec", "hello", "--timeout", "5"], monkeypatch
        )
        assert code == 0
        assert err == ""
