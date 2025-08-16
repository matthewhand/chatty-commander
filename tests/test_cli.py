import sys
import types

# Patch sys.modules to mock openwakeword and openwakeword.model for test imports
sys.modules['openwakeword'] = types.ModuleType('openwakeword')
mock_model_mod = types.ModuleType('openwakeword.model')
mock_model_mod.Model = type('Model', (), {})
sys.modules['openwakeword.model'] = mock_model_mod
import os  # noqa: E402 - import after sys.modules patching for test setup
import sys  # noqa: E402 - import after sys.modules patching for test setup
from unittest.mock import patch  # noqa: E402 - import after test setup

import pytest  # noqa: E402 - import after test setup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa: E402 - path manipulation before imports

from chatty_commander.cli.cli import cli_main  # noqa: E402 - imported after path setup


def test_cli_run(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'run'])
    with patch('chatty_commander.cli.cli.run_app') as mock_run:
        cli_main()
        mock_run.assert_called_once()


def test_cli_config_interactive(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--interactive'])
    with patch('chatty_commander.cli.cli.ConfigCLI.interactive_mode') as mock_interactive:
        cli_main()
        mock_interactive.assert_called_once()


def test_cli_config_list(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--list'])
    with patch('chatty_commander.cli.cli.ConfigCLI.list_config') as mock_list:
        cli_main()
        mock_list.assert_called_once()


def test_cli_set_state_model(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, 'argv', ['cli.py', 'config', '--set-state-model', 'idle', 'model1,model2']
    )
    with patch('chatty_commander.cli.cli.ConfigCLI.set_state_model') as mock_set:
        cli_main()
        mock_set.assert_called_with('idle', 'model1,model2')


def test_cli_set_listen_for(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-listen-for', 'param1', 'value1'])
    with patch('chatty_commander.cli.cli.ConfigCLI.set_listen_for') as mock_set:
        cli_main()
        mock_set.assert_called_with('param1', 'value1')


def test_cli_set_mode(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-mode', 'mode1', 'option1'])
    with patch('chatty_commander.cli.cli.ConfigCLI.set_mode'):
        with pytest.raises(SystemExit):
            cli_main()
        mock_set.assert_not_called()
    captured = capsys.readouterr()
    assert "Invalid mode" in captured.err


def test_cli_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    # Patch input to immediately exit the shell
    monkeypatch.setattr('builtins.input', lambda _: 'exit')
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert 'ChattyCommander Interactive Shell' in captured.out
    assert 'exit' in captured.out or 'Exiting shell.' in captured.out


def test_cli_config_wizard(monkeypatch):
    # Simulate: chatty-commander config wizard
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', 'wizard'])
    with patch('chatty_commander.cli.cli.ConfigCLI.run_wizard') as mock_wizard:
        cli_main()
        mock_wizard.assert_called_once()


def test_cli_interactive_shell_exit(monkeypatch):
    # Simulate running with no arguments, then typing 'exit'
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    inputs = iter(['exit'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    # Patch parser.print_help to avoid printing
    with patch('chatty_commander.cli.cli.HelpfulArgumentParser.print_help'):
        with pytest.raises(SystemExit):
            cli_main()


def test_cli_argument_validation_invalid_model(monkeypatch, capsys):
    # --set-model-action with invalid model
    monkeypatch.setattr(
        sys, 'argv', ['cli.py', 'config', '--set-model-action', 'invalid_model', 'summarize']
    )
    with patch('chatty_commander.cli.cli.ConfigCLI.set_model_action'):
        with pytest.raises(SystemExit):
            cli_main()
    captured = capsys.readouterr()
    assert "Invalid model name" in captured.err


def test_cli_system_update_check(monkeypatch):
    # Simulate: chatty-commander system updates check
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'system', 'updates', 'check'])
    with patch(
        'chatty_commander.app.config.Config.perform_update_check',
        return_value={"updates_available": False, "update_count": 0},
    ):
        with patch('builtins.print') as mock_print:
            cli_main()
            mock_print.assert_any_call("No updates available.")


def test_cli_system_start_on_boot_enable(monkeypatch):
    # Simulate: chatty-commander system start-on-boot enable
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'system', 'start-on-boot', 'enable'])
    with patch('chatty_commander.app.config.Config.set_start_on_boot') as mock_set:
        with patch('builtins.print') as mock_print:
            cli_main()
            mock_set.assert_called_with(True)
            mock_print.assert_any_call("Start on boot enabled successfully.")


def test_cli_list_text_output(monkeypatch, capsys):
    import sys
    import types

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    # Arrange minimal config with model_actions
    class DummyConfig:
        model_actions = {'hello': {'shell': 'echo hello'}, 'web': {'url': 'http://localhost'}}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    # Invoke CLI
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'list'])
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    with __import__('unittest').mock.patch('builtins.print') as mock_print:
        cli_main()
        # Should print a header and the command names
        printed = " ".join(str(args[0]) for args, _ in mock_print.call_args_list if args)
        assert 'Available commands' in printed
        assert 'hello' in printed and 'web' in printed


def test_cli_list_json_output(monkeypatch, capsys):
    import json
    import sys
    import types

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    class DummyConfig:
        model_actions = {'cmd1': {'shell': 'echo 1'}, 'cmd2': {'keypress': 'a'}}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    monkeypatch.setattr(sys, 'argv', ['cli.py', 'list', '--json'])
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    cli_main()
    captured = capsys.readouterr()
    # Output should be valid JSON array
    data = json.loads(captured.out.strip() or "[]")
    assert isinstance(data, list)
    names = [item.get('name') for item in data]
    assert 'cmd1' in names and 'cmd2' in names


def test_cli_list_empty_config(monkeypatch, capsys):
    import sys
    import types

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    class DummyConfig:
        model_actions = {}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    monkeypatch.setattr(sys, 'argv', ['cli.py', 'list'])
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    with __import__('unittest').mock.patch('builtins.print') as mock_print:
        cli_main()
        printed = " ".join(str(args[0]) for args, _ in mock_print.call_args_list if args)
        assert 'No commands configured' in printed


def test_cli_exec_known_command_dry_run(monkeypatch, capsys):
    import sys
    import types

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    class DummyConfig:
        model_actions = {'say': {'shell': 'echo hi'}}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    # Dry-run should not invoke executor
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'exec', 'say', '--dry-run'])
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    with __import__('unittest').mock.patch('chatty_commander.cli.cli.CommandExecutor') as mock_exec:
        cli_main()
        assert not mock_exec.called
    captured = capsys.readouterr()
    assert 'DRY RUN' in captured.out and 'say' in captured.out


def test_cli_exec_unknown_command(monkeypatch, capsys):
    import sys
    import types

    import pytest

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    class DummyConfig:
        model_actions = {'known': {'shell': 'echo ok'}}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    monkeypatch.setattr(sys, 'argv', ['cli.py', 'exec', 'unknown'])
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    with pytest.raises(SystemExit) as ei:
        cli_main()
    assert ei.value.code == 1
    captured = capsys.readouterr()
    assert 'Unknown command' in captured.err


def test_cli_exec_timeout_flag_passthrough(monkeypatch):
    import sys
    import types

    sys.modules['openwakeword'] = types.ModuleType('openwakeword')
    mock_model_mod = types.ModuleType('openwakeword.model')
    mock_model_mod.Model = type('Model', (), {})
    sys.modules['openwakeword.model'] = mock_model_mod

    class DummyConfig:
        model_actions = {'t': {'shell': 'sleep 5'}}

    monkeypatch.setattr('chatty_commander.app.config.Config', lambda: DummyConfig())

    monkeypatch.setattr(sys, 'argv', ['cli.py', 'exec', 't', '--timeout', '2'])
    # Ensure we call CommandExecutor and pass through timeout; we won't actually sleep in tests
    from chatty_commander.cli.cli import cli_main  # noqa: E402

    with __import__('unittest').mock.patch('chatty_commander.cli.cli.CommandExecutor') as MockExec:
        instance = MockExec.return_value
        cli_main()
        # Expect executor to be asked to run the command; our CLI layer will call execute_command(name)
        instance.execute_command.assert_called_with('t')
