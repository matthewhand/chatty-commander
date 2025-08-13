import io
import json
import sys

import pytest

from chatty_commander.cli.cli import cli_main


class DummyConfigDirect:
    def __init__(self, actions):
        # Intentionally set instance attribute so cli resolution uses __dict__ directly
        self.model_actions = actions


@pytest.fixture
def replace_config_with_dummy(monkeypatch):
    def _factory(actions):
        def _dummy_config_ctor():
            return DummyConfigDirect(actions)

        # Patch where cli imports Config inside functions: config.Config
        import chatty_commander.app.config as config_module

        monkeypatch.setattr(
            config_module, "Config", staticmethod(lambda: DummyConfigDirect(actions))
        )

        return _dummy_config_ctor

    return _factory


def run_cli_main_with_args(args_list, monkeypatch):
    # Simulate CLI invocation by patching sys.argv
    monkeypatch.setattr(sys, "argv", ["chatty-commander"] + args_list)
    # Capture stdout/stderr
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


def test_cli_list_respects_monkeypatched_config_text(monkeypatch, replace_config_with_dummy):
    actions = {
        "hello": {"shell": {"cmd": "echo hello"}},
        "web": {"url": {"url": "https://example.com"}},
    }
    replace_config_with_dummy(actions)
    code, out, err = run_cli_main_with_args(["list"], monkeypatch)
    assert code == 0
    # Expected header and sorted names
    lines = [ln.rstrip() for ln in out.strip().splitlines()]
    assert lines[0] == "Available commands:"
    # ensure both names present
    assert "- hello" in lines
    assert "- web" in lines
    # stderr empty
    assert err == ""


def test_cli_list_respects_monkeypatched_config_json(monkeypatch, replace_config_with_dummy):
    actions = {
        "cmd1": {"shell": {"cmd": "true"}},
        "cmd2": {"url": {"url": "https://x"}},
    }
    replace_config_with_dummy(actions)
    code, out, err = run_cli_main_with_args(["list", "--json"], monkeypatch)
    assert code == 0
    data = json.loads(out.strip())
    # Expect list of dicts with name and type keys
    names = {d["name"] for d in data}
    types = {d["type"] for d in data}
    assert names == {"cmd1", "cmd2"}
    assert "shell" in types and "url" in types
    assert err == ""


def test_cli_list_empty_config(monkeypatch, replace_config_with_dummy):
    replace_config_with_dummy({})
    code, out, err = run_cli_main_with_args(["list"], monkeypatch)
    assert code == 0
    assert out.strip() == "No commands configured."
    assert err == ""


def test_cli_exec_unknown_command_exit_and_stderr(monkeypatch, replace_config_with_dummy):
    replace_config_with_dummy({"known": {"shell": {"cmd": "echo ok"}}})
    code, out, err = run_cli_main_with_args(["exec", "missing"], monkeypatch)
    # unknown should exit with code 1 and write to stderr
    assert code == 1
    assert out == ""
    assert "Unknown command: missing" in err


def test_cli_exec_known_command_dry_run(monkeypatch, replace_config_with_dummy):
    actions = {"hello": {"shell": {"cmd": "echo hi"}}}
    replace_config_with_dummy(actions)
    code, out, err = run_cli_main_with_args(["exec", "hello", "--dry-run"], monkeypatch)
    assert code == 0
    assert "DRY RUN: would execute command 'hello'" in out
    assert err == ""


def test_cli_exec_invokes_executor(monkeypatch, replace_config_with_dummy):
    actions = {"hello": {"shell": {"cmd": "echo hi"}}}
    replace_config_with_dummy(actions)

    called = {"count": 0, "last": None}

    class FakeExecutor:
        def __init__(self, cfg, a, b):
            self.cfg = cfg

        def execute_command(self, name):
            called["count"] += 1
            called["last"] = name

    monkeypatch.setattr('chatty_commander.cli.cli.CommandExecutor', FakeExecutor)

    code, out, err = run_cli_main_with_args(["exec", "hello"], monkeypatch)
    assert code == 0
    assert called["count"] == 1
    assert called["last"] == "hello"
    assert err == ""


def test_cli_exec_timeout_flag_passthrough_no_error(monkeypatch, replace_config_with_dummy):
    # The timeout flag is accepted by CLI; per-command handling occurs inside executor.
    actions = {"hello": {"shell": {"cmd": "sleep 0"}}}
    replace_config_with_dummy(actions)

    class NoopExecutor:
        def __init__(self, cfg, a, b):
            pass

        def execute_command(self, name):
            return

    monkeypatch.setattr(
        'chatty_commander.app.command_executor.CommandExecutor', NoopExecutor
    )

    code, out, err = run_cli_main_with_args(["exec", "hello", "--timeout", "5"], monkeypatch)
    assert code == 0
    # No specific stdout expected in non-dry-run success
    assert err == ""
