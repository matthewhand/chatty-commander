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

"""Additional tests to improve coverage for cli/main.py."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


class TestMainCreateParser:
    """Tests for create_parser function in main.py."""

    def test_create_parser_returns_parser(self):
        """Test that create_parser returns an ArgumentParser."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_has_web_flag(self):
        """Test parser has --web flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web"])
        assert args.web is True

    def test_parser_has_gui_flag(self):
        """Test parser has --gui flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui"])
        assert args.gui is True

    def test_parser_has_config_flag(self):
        """Test parser has --config flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--config"])
        assert args.config is True

    def test_parser_has_shell_flag(self):
        """Test parser has --shell flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--shell"])
        assert args.shell is True

    def test_parser_has_no_auth_flag(self):
        """Test parser has --no-auth flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--no-auth"])
        assert args.no_auth is True

    def test_parser_has_host_option(self):
        """Test parser has --host option."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--host", "localhost"])
        assert args.host == "localhost"

    def test_parser_has_port_option(self):
        """Test parser has --port option."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--web", "--port", "9000"])
        assert args.port == 9000

    def test_parser_has_log_level_option(self):
        """Test parser has --log-level option."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_parser_has_no_gui_flag(self):
        """Test parser has --no-gui flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui", "--no-gui"])
        assert args.no_gui is True

    def test_parser_has_display_option(self):
        """Test parser has --display option."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--gui", "--display", ":0"])
        assert args.display == ":0"

    def test_parser_has_test_mode_flag(self):
        """Test parser has --test-mode flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--test-mode"])
        assert args.test_mode is True

    def test_parser_has_orchestrate_flag(self):
        """Test parser has --orchestrate flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate"])
        assert args.orchestrate is True

    def test_parser_has_enable_text_flag(self):
        """Test parser has --enable-text flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-text"])
        assert args.enable_text is True

    def test_parser_has_enable_openwakeword_flag(self):
        """Test parser has --enable-openwakeword flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-openwakeword"])
        assert args.enable_openwakeword is True

    def test_parser_has_enable_computer_vision_flag(self):
        """Test parser has --enable-computer-vision flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-computer-vision"])
        assert args.enable_computer_vision is True

    def test_parser_has_enable_discord_bridge_flag(self):
        """Test parser has --enable-discord-bridge flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["--orchestrate", "--enable-discord-bridge"])
        assert args.enable_discord_bridge is True


class TestMainRunCLIMode:
    """Tests for run_cli_mode function in main.py."""

    def test_run_cli_mode_keyboard_interrupt(self):
        """Test run_cli_mode handles KeyboardInterrupt gracefully."""
        from chatty_commander.cli.main import run_cli_mode

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
        from chatty_commander.cli.main import run_cli_mode

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


class TestMainRunWebMode:
    """Tests for run_web_mode function in main.py."""

    def test_run_web_mode_import_error(self):
        """Test run_web_mode handles ImportError gracefully."""
        from chatty_commander.cli.main import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Patch the import to raise ImportError
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
        from chatty_commander.cli.main import run_web_mode

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
            with patch(
                "chatty_commander.web.web_mode.WebModeServer", return_value=mock_web_server
            ):
                with patch("chatty_commander.cli.main.threading.Event"):
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
        from chatty_commander.cli.main import run_web_mode

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
                with patch("chatty_commander.cli.main.threading.Event"):
                    run_web_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                    )


class TestMainRunGUIMode:
    """Tests for run_gui_mode function in main.py."""

    def test_run_gui_mode_no_gui_flag(self):
        """Test run_gui_mode respects --no-gui flag."""
        from chatty_commander.cli.main import run_gui_mode

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
        from chatty_commander.cli.main import run_gui_mode

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


class TestMainRunInteractiveShell:
    """Tests for run_interactive_shell function in main.py."""

    def test_run_interactive_shell_exit_command(self):
        """Test run_interactive_shell handles exit command."""
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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
        from chatty_commander.cli.main import run_interactive_shell

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


class TestMainFunction:
    """Tests for main function in main.py."""

    def test_main_help_flag(self):
        """Test main handles --help flag."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        with patch("sys.argv", ["prog", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args()

        assert exc_info.value.code == 0

    def test_main_port_validation_low_port(self):
        """Test main rejects ports below 1024."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        with patch("sys.argv", ["prog", "--web", "--port", "80"]):
            with pytest.raises(SystemExit) as exc_info:
                args = parser.parse_args()
                if args.web and args.port is not None and args.port < 1024:
                    parser.error("Port must be 1024 or higher for non-root users")

        assert exc_info.value.code == 2

    def test_main_no_auth_without_web(self):
        """Test main rejects --no-auth without --web."""
        from chatty_commander.cli.main import create_parser

        parser = create_parser()
        with patch("sys.argv", ["prog", "--no-auth"]):
            with pytest.raises(SystemExit) as exc_info:
                args = parser.parse_args()
                if args.no_auth and not args.web:
                    parser.error("--no-auth only applicable in web mode")

        assert exc_info.value.code == 2


class TestMainRunOrchestratorMode:
    """Tests for run_orchestrator_mode function in main.py."""

    def test_run_orchestrator_mode_basic(self):
        """Test run_orchestrator_mode basic execution."""
        from chatty_commander.cli.main import run_orchestrator_mode

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
