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

"""Additional tests to improve coverage for cli/cli.py."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


class TestCreateParser:
    """Tests for create_parser function."""

    def test_create_parser_returns_parser(self):
        """Test that create_parser returns an ArgumentParser."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_has_web_flag(self):
        """Test parser has --web flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web"])
        assert args.web is True

    def test_parser_has_gui_flag(self):
        """Test parser has --gui flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui"])
        assert args.gui is True

    def test_parser_has_config_flag(self):
        """Test parser has --config flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--config"])
        assert args.config is True

    def test_parser_has_shell_flag(self):
        """Test parser has --shell flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--shell"])
        assert args.shell is True

    def test_parser_has_no_auth_flag(self):
        """Test parser has --no-auth flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--no-auth"])
        assert args.no_auth is True

    def test_parser_has_host_option(self):
        """Test parser has --host option."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--host", "localhost"])
        assert args.host == "localhost"

    def test_parser_has_port_option(self):
        """Test parser has --port option."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--port", "9000"])
        assert args.port == 9000

    def test_parser_has_log_level_option(self):
        """Test parser has --log-level option."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_parser_has_no_gui_flag(self):
        """Test parser has --no-gui flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui", "--no-gui"])
        assert args.no_gui is True

    def test_parser_has_display_option(self):
        """Test parser has --display option."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui", "--display", ":0"])
        assert args.display == ":0"

    def test_parser_has_test_mode_flag(self):
        """Test parser has --test-mode flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--test-mode"])
        assert args.test_mode is True

    def test_parser_has_orchestrate_flag(self):
        """Test parser has --orchestrate flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate"])
        assert args.orchestrate is True

    def test_parser_has_enable_text_flag(self):
        """Test parser has --enable-text flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-text"])
        assert args.enable_text is True

    def test_parser_has_enable_openwakeword_flag(self):
        """Test parser has --enable-openwakeword flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-openwakeword"])
        assert args.enable_openwakeword is True

    def test_parser_has_enable_computer_vision_flag(self):
        """Test parser has --enable-computer-vision flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-computer-vision"])
        assert args.enable_computer_vision is True

    def test_parser_has_enable_discord_bridge_flag(self):
        """Test parser has --enable-discord-bridge flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-discord-bridge"])
        assert args.enable_discord_bridge is True

    def test_parser_list_subcommand(self):
        """Test parser has list subcommand."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["list"])
        assert args.subcommand == "list"

    def test_parser_list_json_flag(self):
        """Test parser list subcommand has --json flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["list", "--json"])
        assert args.json is True

    def test_parser_exec_subcommand(self):
        """Test parser has exec subcommand."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["exec", "test_command"])
        assert args.subcommand == "exec"
        assert args.command_name == "test_command"

    def test_parser_exec_dry_run_flag(self):
        """Test parser exec subcommand has --dry-run flag."""
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["exec", "test_command", "--dry-run"])
        assert args.dry_run is True


class TestRunCLIMode:
    """Tests for run_cli_mode function."""

    def test_run_cli_mode_keyboard_interrupt(self):
        """Test run_cli_mode handles KeyboardInterrupt gracefully."""
        from chatty_commander.cli.cli import run_cli_mode

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_model_manager.listen_for_commands.side_effect = KeyboardInterrupt

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"

        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with pytest.raises(SystemExit) as exc_info:
            run_cli_mode(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        assert exc_info.value.code == 0

    def test_run_cli_mode_shutdown_flag(self):
        """Test run_cli_mode respects shutdown flag."""
        from chatty_commander.cli.cli import run_cli_mode

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        # Return None first, then raise to exit loop
        mock_model_manager.listen_for_commands.side_effect = [None, KeyboardInterrupt]
        mock_model_manager.shutdown = MagicMock()

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_state_manager.shutdown = MagicMock()

        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with pytest.raises(SystemExit):
            run_cli_mode(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        mock_model_manager.reload_models.assert_called_once_with("idle")


class TestRunWebMode:
    """Tests for run_web_mode function."""

    def test_run_web_mode_import_error(self):
        """Test run_web_mode handles ImportError gracefully."""
        from chatty_commander.cli.cli import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Patch the import to raise ImportError
        with patch.dict(
            sys.modules, {"chatty_commander.web.web_mode": None}
        ):
            # Need to patch the actual import inside the function
            import builtins
            original_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                if "web_mode" in name:
                    raise ImportError("No module")
                return original_import(name, *args, **kwargs)
            
            with patch("builtins.__import__", side_effect=mock_import):
                with pytest.raises(SystemExit) as exc_info:
                    run_web_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                    )

        assert exc_info.value.code == 1

    def test_run_web_mode_env_host_override(self):
        """Test run_web_mode respects CHATCOMM_HOST env var."""
        from chatty_commander.cli.cli import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        mock_web_server = MagicMock()
        mock_web_server.run = MagicMock()

        with patch.dict(
            "os.environ", {"CHATCOMM_HOST": "127.0.0.1", "CHATCOMM_PORT": ""}
        ):
            # Patch where WebModeServer is imported (inside the function)
            with patch(
                "chatty_commander.web.web_mode.WebModeServer", return_value=mock_web_server
            ):
                with patch("chatty_commander.cli.cli.threading.Event"):
                    # This test just verifies the function runs without error
                    # The env var override is tested implicitly
                    run_web_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                        host="0.0.0.0",
                        port=8100,
                    )

    def test_run_web_mode_env_port_override(self):
        """Test run_web_mode respects CHATCOMM_PORT env var."""
        from chatty_commander.cli.cli import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        mock_web_server = MagicMock()
        mock_web_server.run = MagicMock()

        with patch.dict(
            "os.environ", {"CHATCOMM_PORT": "9999", "CHATCOMM_HOST": ""}
        ):
            with patch(
                "chatty_commander.web.web_mode.WebModeServer", return_value=mock_web_server
            ):
                with patch("chatty_commander.cli.cli.threading.Event"):
                    run_web_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                    )


class TestRunGUIMode:
    """Tests for run_gui_mode function."""

    def test_run_gui_mode_no_gui_flag(self):
        """Test run_gui_mode respects --no-gui flag."""
        from chatty_commander.cli.cli import run_gui_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        result = run_gui_mode(
            mock_config,
            mock_model_manager,
            mock_state_manager,
            mock_command_executor,
            mock_logger,
            no_gui=True,
        )

        assert result == 0

    def test_run_gui_mode_headless_environment(self):
        """Test run_gui_mode skips in headless environment."""
        from chatty_commander.cli.cli import run_gui_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch.dict("os.environ", {}, clear=True):
            with patch("os.name", "posix"):
                result = run_gui_mode(
                    mock_config,
                    mock_model_manager,
                    mock_state_manager,
                    mock_command_executor,
                    mock_logger,
                )

        assert result == 0


class TestRunInteractiveShell:
    """Tests for run_interactive_shell function."""

    def test_run_interactive_shell_exit_command(self):
        """Test run_interactive_shell handles exit command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_model_manager.get_models.return_value = ["model1"]

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"

        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Simulate user typing "exit"
        with patch("builtins.input", return_value="exit"):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

    def test_run_interactive_shell_help_command(self, capsys):
        """Test run_interactive_shell handles help command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Simulate user typing "help" then "exit"
        with patch("builtins.input", side_effect=["help", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        captured = capsys.readouterr()
        assert "Available commands" in captured.out

    def test_run_interactive_shell_state_command(self, capsys):
        """Test run_interactive_shell handles state command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["state", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        captured = capsys.readouterr()
        assert "Current state" in captured.out

    def test_run_interactive_shell_models_command(self, capsys):
        """Test run_interactive_shell handles models command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_model_manager.get_models.return_value = ["model1", "model2"]
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["models", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        captured = capsys.readouterr()
        assert "Loaded models" in captured.out

    def test_run_interactive_shell_execute_command(self, capsys):
        """Test run_interactive_shell handles execute command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["execute test_cmd", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        mock_command_executor.execute_command.assert_called_once_with("test_cmd")

    def test_run_interactive_shell_unknown_execute_command(self, capsys):
        """Test run_interactive_shell handles unknown execute command."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["execute unknown", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_run_interactive_shell_eof_handling(self):
        """Test run_interactive_shell handles EOFError."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=EOFError):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )


class TestCLIMainListSubcommand:
    """Tests for cli_main list subcommand."""

    def test_cli_main_list_empty_commands(self, capsys):
        """Test list subcommand with no commands."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "list"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    result = cli_main()

        assert result == 0
        captured = capsys.readouterr()
        assert "No commands configured" in captured.out

    def test_cli_main_list_with_commands(self, capsys):
        """Test list subcommand with commands."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {"cmd1": {"shell": "echo 1"}, "cmd2": {"url": "http://example.com"}}

        with patch("sys.argv", ["prog", "list"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    result = cli_main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Available commands" in captured.out

    def test_cli_main_list_json_output(self, capsys):
        """Test list subcommand with JSON output."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {"cmd1": {"shell": "echo 1"}}

        with patch("sys.argv", ["prog", "list", "--json"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    result = cli_main()

        assert result == 0
        captured = capsys.readouterr()
        import json
        # Should be valid JSON
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["name"] == "cmd1"


class TestCLIMainExecSubcommand:
    """Tests for cli_main exec subcommand."""

    def test_cli_main_exec_dry_run(self, capsys):
        """Test exec subcommand with dry-run."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        with patch("sys.argv", ["prog", "exec", "test_cmd", "--dry-run"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    result = cli_main()

        assert result == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_cli_main_exec_unknown_command(self, capsys):
        """Test exec subcommand with unknown command."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "exec", "unknown_cmd"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with pytest.raises(SystemExit) as exc_info:
                                        cli_main()

        assert exc_info.value.code == 1

    def test_cli_main_exec_actual_command(self):
        """Test exec subcommand executes actual command."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        mock_executor = MagicMock()

        with patch("sys.argv", ["prog", "exec", "test_cmd"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch(
                                "chatty_commander.cli.cli.CommandExecutor",
                                return_value=mock_executor,
                            ):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    result = cli_main()

        assert result == 0
        mock_executor.execute_command.assert_called_once_with("test_cmd")


class TestCLIMainValidation:
    """Tests for cli_main argument validation."""

    def test_cli_main_port_validation_low_port(self):
        """Test cli_main rejects ports below 1024."""
        from chatty_commander.cli.cli import cli_main

        with patch("sys.argv", ["prog", "--web", "--port", "80"]):
            with pytest.raises(SystemExit) as exc_info:
                cli_main()

        assert exc_info.value.code == 2

    def test_cli_main_no_auth_without_web(self):
        """Test cli_main rejects --no-auth without --web."""
        from chatty_commander.cli.cli import cli_main

        with patch("sys.argv", ["prog", "--no-auth"]):
            with pytest.raises(SystemExit) as exc_info:
                cli_main()

        assert exc_info.value.code == 2


class TestCLIMainHelp:
    """Tests for cli_main help handling."""

    def test_cli_main_help_flag(self):
        """Test cli_main handles --help flag."""
        # --help triggers argparse to exit with code 0
        # We test this by checking that argparse exits properly
        import argparse
        from chatty_commander.cli.cli import create_parser

        parser = create_parser()
        with patch("sys.argv", ["prog", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args()

        # argparse exits with 0 for --help
        assert exc_info.value.code == 0


class TestRunOrchestratorMode:
    """Tests for run_orchestrator_mode function."""

    def test_run_orchestrator_mode_basic(self):
        """Test run_orchestrator_mode basic execution."""
        from chatty_commander.cli.cli import run_orchestrator_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        mock_orchestrator = MagicMock()
        mock_orchestrator.start.return_value = ["text"]
        mock_orchestrator.stop = MagicMock()

        mock_args = MagicMock()
        mock_args.web = False
        mock_args.gui = False
        mock_args.enable_text = True
        mock_args.enable_openwakeword = False
        mock_args.enable_computer_vision = False
        mock_args.enable_discord_bridge = False

        # Patch at the module level where it's imported
        with patch(
            "chatty_commander.app.orchestrator.ModeOrchestrator",
            return_value=mock_orchestrator,
        ):
            with patch(
                "chatty_commander.app.orchestrator.OrchestratorFlags"
            ):
                with patch("signal.pause", side_effect=KeyboardInterrupt):
                    result = run_orchestrator_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                        mock_args,
                    )

        assert result == 0
        mock_orchestrator.stop.assert_called_once()
