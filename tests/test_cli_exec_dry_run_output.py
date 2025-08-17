import io
import sys

from src.chatty_commander.cli.cli import cli_main


def test_cli_exec_dry_run_prints_action(monkeypatch):
    # Patch Config to return a known model_actions mapping
    import chatty_commander.app.config as config_module

    from src.chatty_commander.cli import cli as cli_module

    class DummyCfg:
        def __init__(self):
            self.model_actions = {"hello": {"shell": {"cmd": "echo hi"}}}

    # Patch both the config module and the _resolve_Config function
    monkeypatch.setattr(config_module, "Config", DummyCfg)
    monkeypatch.setattr(cli_module, "_resolve_Config", lambda: DummyCfg)

    # Simulate CLI invocation
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "exec", "hello", "--dry-run"])

    stdout = io.StringIO()
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    try:
        cli_main()
    except SystemExit as e:
        assert e.code in (0, None)

    out = stdout.getvalue()
    assert "DRY RUN: would execute command 'hello'" in out
