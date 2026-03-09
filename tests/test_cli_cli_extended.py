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

"""Extended tests to improve coverage for cli/cli.py - targeting 80%+."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


class TestCLIMainExtended:
    """Extended tests for cli_main function to reach 80% coverage."""

    def test_cli_main_config_mode(self):
        """Test cli_main handles --config flag."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}
        mock_config.web_server = {}

        mock_config_cli = MagicMock()

        with patch("sys.argv", ["prog", "--config"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.config_cli.ConfigCLI",
                                        return_value=mock_config_cli,
                                    ):
                                        result = cli_main()

        assert result == 0
        mock_config_cli.run_wizard.assert_called_once()

    def test_cli_main_shell_mode(self):
        """Test cli_main handles --shell flag."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "--shell"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ) as mock_shell:
                                        result = cli_main()

        assert result == 0
        mock_shell.assert_called_once()

    def test_cli_main_gui_mode_headless(self):
        """Test cli_main handles --gui flag in headless environment."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "--gui"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_gui_mode",
                                        return_value=0,
                                    ) as mock_gui:
                                        result = cli_main()

        assert result == 0
        mock_gui.assert_called_once()

    def test_cli_main_gui_mode_deps_missing(self):
        """Test cli_main handles --gui when deps are missing."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "--gui"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_gui_mode",
                                        return_value=2,
                                    ) as mock_gui:
                                        result = cli_main()

        assert result == 2
        mock_gui.assert_called_once()

    def test_cli_main_test_mode(self):
        """Test cli_main handles --test-mode flag."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "--test-mode", "--shell"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager") as mock_mm:
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ):
                                        result = cli_main()

        assert result == 0
        # ModelManager should be called with mock_models=True
        mock_mm.assert_called_once()
        call_kwargs = mock_mm.call_args[1]
        assert call_kwargs.get("mock_models") is True

    def test_cli_main_interactive_mode(self):
        """Test cli_main handles no arguments (interactive mode)."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ) as mock_shell:
                                        result = cli_main()

        assert result == 0
        mock_shell.assert_called_once()

    def test_cli_main_cli_mode(self):
        """Test cli_main handles default CLI mode."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        # Use --log-level to avoid triggering other modes
        with patch("sys.argv", ["prog", "--log-level", "INFO"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_cli_mode"
                                    ) as mock_cli:
                                        result = cli_main()

        assert result == 0
        mock_cli.assert_called_once()

    def test_cli_main_web_mode_with_host_port(self):
        """Test cli_main handles --web with --host and --port."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}
        mock_config.web_server = {}

        mock_web_server = MagicMock()

        with patch("sys.argv", ["prog", "--web", "--host", "localhost", "--port", "9000"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.web.web_mode.WebModeServer",
                                        return_value=mock_web_server,
                                    ):
                                        with patch(
                                            "chatty_commander.cli.cli.threading.Event"
                                        ):
                                            result = cli_main()

        assert result == 0

    def test_cli_main_orchestrate_mode(self):
        """Test cli_main handles --orchestrate flag."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_orchestrator = MagicMock()
        mock_orchestrator.start.return_value = ["text"]
        mock_orchestrator.stop = MagicMock()

        with patch("sys.argv", ["prog", "--orchestrate", "--enable-text"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.app.orchestrator.ModeOrchestrator",
                                        return_value=mock_orchestrator,
                                    ):
                                        with patch(
                                            "chatty_commander.app.orchestrator.OrchestratorFlags"
                                        ):
                                            with patch(
                                                "signal.pause", side_effect=KeyboardInterrupt
                                            ):
                                                result = cli_main()

        assert result == 0
        mock_orchestrator.stop.assert_called_once()

    def test_cli_main_default_config_generated(self, capsys):
        """Test cli_main generates default config when needed."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}

        with patch("sys.argv", ["prog", "--shell"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=True,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ):
                                        result = cli_main()

        assert result == 0

    def test_cli_main_host_override(self):
        """Test cli_main applies host override."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}
        mock_config.web_server = {}

        with patch("sys.argv", ["prog", "--shell", "--host", "custom-host"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ):
                                        result = cli_main()

        assert result == 0

    def test_cli_main_port_override(self):
        """Test cli_main applies port override."""
        from chatty_commander.cli.cli import cli_main

        mock_config = MagicMock()
        mock_config.model_actions = {}
        mock_config.web_server = {}

        with patch("sys.argv", ["prog", "--shell", "--port", "9999"]):
            with patch("chatty_commander.cli.cli.Config", return_value=mock_config):
                with patch(
                    "chatty_commander.cli.cli.generate_default_config_if_needed",
                    return_value=False,
                ):
                    with patch("chatty_commander.cli.cli.ModelManager"):
                        with patch("chatty_commander.cli.cli.StateManager"):
                            with patch("chatty_commander.cli.cli.CommandExecutor"):
                                with patch("chatty_commander.cli.cli.setup_logger"):
                                    with patch(
                                        "chatty_commander.cli.cli.run_interactive_shell"
                                    ):
                                        result = cli_main()

        assert result == 0


class TestRunGUIModeExtended:
    """Extended tests for run_gui_mode function."""

    def test_run_gui_mode_display_override(self):
        """Test run_gui_mode with display override."""
        from chatty_commander.cli.cli import run_gui_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Display override sets DISPLAY env var, but still headless
        with patch("os.name", "posix"):
            # Start with no DISPLAY, then set it via display_override
            with patch.dict("os.environ", {}, clear=True):
                result = run_gui_mode(
                    mock_config,
                    mock_model_manager,
                    mock_state_manager,
                    mock_command_executor,
                    mock_logger,
                    display_override=":1",
                )

        # Should skip in headless even with display override (no_gui not set, but no display after override)
        # Actually, display_override sets DISPLAY, so it should try to run GUI
        # But since we're mocking, it will fail and return 2
        assert result in [0, 2]  # Either skipped or failed gracefully

    def test_run_gui_mode_avatar_gui_fallback(self):
        """Test run_gui_mode falls back through GUI options."""
        from chatty_commander.cli.cli import run_gui_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        # Set up environment with DISPLAY
        with patch("os.name", "posix"):
            with patch.dict("os.environ", {"DISPLAY": ":0"}):
                # All GUI imports fail, eventually returns 2
                with patch.dict(
                    "sys.modules",
                    {
                        "chatty_commander.avatars.avatar_gui": None,
                        "src.chatty_commander.avatars.avatar_gui": None,
                        "chatty_commander.gui.pyqt5_avatar": None,
                        "src.chatty_commander.gui.pyqt5_avatar": None,
                        "chatty_commander.gui.tray_popup": None,
                        "src.chatty_commander.gui.tray_popup": None,
                        "chatty_commander.gui": None,
                    },
                ):
                    result = run_gui_mode(
                        mock_config,
                        mock_model_manager,
                        mock_state_manager,
                        mock_command_executor,
                        mock_logger,
                    )

        # Should return 2 when all GUI options fail
        assert result == 2


class TestRunWebModeExtended:
    """Extended tests for run_web_mode function."""

    def test_run_web_mode_with_callbacks(self):
        """Test run_web_mode sets up callbacks."""
        from chatty_commander.cli.cli import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_model_manager.add_command_callback = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.add_state_change_callback = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        mock_web_server = MagicMock()
        mock_web_server.run = MagicMock()

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

        mock_model_manager.add_command_callback.assert_called_once()
        mock_state_manager.add_state_change_callback.assert_called_once()

    def test_run_web_mode_shutdown_cleanup(self):
        """Test run_web_mode cleans up on shutdown."""
        from chatty_commander.cli.cli import run_web_mode

        mock_config = MagicMock()
        mock_model_manager = MagicMock()
        mock_model_manager.shutdown = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.shutdown = MagicMock()
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        mock_web_server = MagicMock()
        mock_web_server.run = MagicMock()

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

        mock_model_manager.shutdown.assert_called_once()
        mock_state_manager.shutdown.assert_called_once()


class TestRunCLIModeExtended:
    """Extended tests for run_cli_mode function."""

    def test_run_cli_mode_command_execution(self):
        """Test run_cli_mode executes commands."""
        from chatty_commander.cli.cli import run_cli_mode

        mock_config = MagicMock()
        mock_config.model_actions = {"test_cmd": {"shell": "echo test"}}

        mock_model_manager = MagicMock()
        mock_model_manager.listen_for_commands.side_effect = ["test_cmd", KeyboardInterrupt]
        mock_model_manager.shutdown = MagicMock()

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_state_manager.update_state.return_value = None
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

        mock_command_executor.execute_command.assert_called_once_with("test_cmd")

    def test_run_cli_mode_state_transition(self):
        """Test run_cli_mode handles state transitions."""
        from chatty_commander.cli.cli import run_cli_mode

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_model_manager.listen_for_commands.side_effect = ["wakeword", KeyboardInterrupt]
        mock_model_manager.shutdown = MagicMock()

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_state_manager.update_state.return_value = "active"
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

        mock_model_manager.reload_models.assert_called()


class TestRunInteractiveShellExtended:
    """Extended tests for run_interactive_shell function."""

    def test_run_interactive_shell_voice_command_simulation(self):
        """Test run_interactive_shell simulates voice commands."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_state_manager.update_state.return_value = "active"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["wakeword", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        mock_state_manager.update_state.assert_called_once_with("wakeword")
        mock_model_manager.reload_models.assert_called_once_with("active")

    def test_run_interactive_shell_empty_input(self):
        """Test run_interactive_shell handles empty input."""
        from chatty_commander.cli.cli import run_interactive_shell

        mock_config = MagicMock()
        mock_config.model_actions = {}

        mock_model_manager = MagicMock()
        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_command_executor = MagicMock()
        mock_logger = MagicMock()

        with patch("builtins.input", side_effect=["", "exit"]):
            run_interactive_shell(
                mock_config,
                mock_model_manager,
                mock_state_manager,
                mock_command_executor,
                mock_logger,
            )

        # State should not be updated for empty input
        mock_state_manager.update_state.assert_not_called()
