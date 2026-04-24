"""Comprehensive tests for CLI entry point and argument parsing.

Tests cover all major CLI flags, argument validation, subcommands,
and error paths.
"""

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

import pytest


class TestConfigFlag:
    """Tests for --config flag behavior."""

    def test_config_flag_triggers_wizard(self, monkeypatch):
        """Ensure that invoking main with --config triggers ConfigCLI.run_wizard."""
        monkeypatch.setattr(sys, "argv", ["main.py", "--config"])
        with (
            patch("config_cli.ConfigCLI.__init__", return_value=None),
            patch("config_cli.ConfigCLI.run_wizard") as mock_wizard,
            patch("chatty_commander.cli.cli.Config"),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
            assert result == 0
            mock_wizard.assert_called_once()


class TestArgumentValidation:
    """Tests for argument validation and error handling."""

    def test_no_auth_without_web_errors(self, monkeypatch):
        """--no-auth without --web should raise error."""
        monkeypatch.setattr(sys, "argv", ["main.py", "--no-auth"])
        with (
            patch("chatty_commander.cli.cli.setup_logger"),
            patch("chatty_commander.cli.cli.Config"),
            pytest.raises(SystemExit) as exc_info,
        ):
            from chatty_commander.cli.cli import cli_main

            cli_main()
        # Should exit with error
        assert exc_info.value.code != 0

    def test_low_port_without_root_errors(self, monkeypatch):
        """Port below 1024 should error for non-root."""
        monkeypatch.setattr(sys, "argv", ["main.py", "--web", "--port", "80"])
        with (
            patch("chatty_commander.cli.cli.setup_logger"),
            patch("chatty_commander.cli.cli.Config"),
            pytest.raises(SystemExit) as exc_info,
        ):
            from chatty_commander.cli.cli import cli_main

            cli_main()
        assert exc_info.value.code != 0


class TestListSubcommand:
    """Tests for list subcommand."""

    def test_list_commands_empty(self, monkeypatch):
        """list subcommand with no commands shows empty message."""
        monkeypatch.setattr(sys, "argv", ["main.py", "list"])
        mock_config = MagicMock()
        mock_config.model_actions = {}

        stdout = io.StringIO()
        with (
            redirect_stdout(stdout),
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
        assert result == 0
        assert "No commands configured" in stdout.getvalue()

    def test_list_commands_text_format(self, monkeypatch):
        """list subcommand shows commands in text format."""
        monkeypatch.setattr(sys, "argv", ["main.py", "list"])
        mock_config = MagicMock()
        mock_config.model_actions = {"cmd1": {}, "cmd2": {}}

        stdout = io.StringIO()
        with (
            redirect_stdout(stdout),
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
        assert result == 0
        output = stdout.getvalue()
        assert "cmd1" in output
        assert "cmd2" in output

    def test_list_commands_json_format(self, monkeypatch):
        """list subcommand with --json outputs JSON."""
        monkeypatch.setattr(sys, "argv", ["main.py", "list", "--json"])
        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        stdout = io.StringIO()
        with (
            redirect_stdout(stdout),
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
        assert result == 0
        import json

        output = json.loads(stdout.getvalue())
        assert isinstance(output, list)
        assert any(c["name"] == "test_cmd" for c in output)


class TestExecSubcommand:
    """Tests for exec subcommand."""

    def test_exec_unknown_command_errors(self, monkeypatch):
        """exec with unknown command should error."""
        monkeypatch.setattr(sys, "argv", ["main.py", "exec", "nonexistent_cmd"])
        mock_config = MagicMock()
        mock_config.model_actions = {}

        stderr = io.StringIO()
        with (
            redirect_stderr(stderr),
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            from chatty_commander.cli.cli import cli_main

            cli_main()
        assert exc_info.value.code == 1

    def test_exec_dry_run(self, monkeypatch):
        """exec with --dry-run should not execute."""
        monkeypatch.setattr(sys, "argv", ["main.py", "exec", "test_cmd", "--dry-run"])
        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        stdout = io.StringIO()
        with (
            redirect_stdout(stdout),
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
        assert result == 0
        assert "DRY RUN" in stdout.getvalue()


class TestModeFlags:
    """Tests for mode selection flags."""

    def test_shell_flag_starts_shell(self, monkeypatch):
        """--shell should call run_interactive_shell."""
        monkeypatch.setattr(sys, "argv", ["main.py", "--shell"])
        with (
            patch("chatty_commander.cli.cli.Config") as mock_config_cls,
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
            patch("chatty_commander.cli.cli.run_interactive_shell") as mock_shell,
        ):
            mock_config = MagicMock()
            mock_config.web_server = {}
            mock_config.model_actions = {}
            mock_config_cls.return_value = mock_config
            mock_shell.return_value = None

            from chatty_commander.cli.cli import cli_main

            result = cli_main()
            assert mock_shell.called
            assert result == 0


class TestTestMode:
    """Tests for --test-mode flag."""

    def test_test_mode_passes_mock_models(self, monkeypatch):
        """--test-mode should pass mock_models=True to ModelManager."""
        monkeypatch.setattr(
            sys, "argv", ["main.py", "--test-mode", "--shell"]
        )
        mock_config = MagicMock()
        mock_config.model_actions = {}

        with (
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager") as mock_mm,
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor"),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
            patch("chatty_commander.cli.cli.run_interactive_shell") as mock_shell,
        ):
            mock_mm.return_value = MagicMock()
            mock_shell.return_value = None

            from chatty_commander.cli.cli import cli_main

            cli_main()
            # ModelManager should be called with mock_models=True
            assert mock_mm.call_args[1]["mock_models"] is True


class TestCRUDIntegration:
    """Integration tests for CLI CRUD operations."""

    def test_exec_valid_command(self, monkeypatch):
        """exec with valid command should execute."""
        monkeypatch.setattr(sys, "argv", ["main.py", "exec", "test_cmd"])

        mock_executor = MagicMock()
        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        with (
            patch("chatty_commander.cli.cli.Config", return_value=mock_config),
            patch("chatty_commander.cli.cli.ModelManager"),
            patch("chatty_commander.cli.cli.StateManager"),
            patch("chatty_commander.cli.cli.CommandExecutor", return_value=mock_executor),
            patch("chatty_commander.cli.cli.setup_logger"),
            patch(
                "chatty_commander.cli.cli.generate_default_config_if_needed",
                return_value=False,
            ),
        ):
            from chatty_commander.cli.cli import cli_main

            result = cli_main()
            assert result == 0
            mock_executor.execute_command.assert_called_once_with("test_cmd")
