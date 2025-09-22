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

"""Focused tests to improve coverage on specific high-impact modules."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


class TestCoverageImprovementFocused:
    @pytest.fixture
    def config(self):
        config = Config()
        config.model_actions = {
            "test_keypress": {"action": "keypress", "keys": "ctrl+c"},
            "test_url": {"action": "url", "url": "http://example.com"},
            "test_custom": {"action": "custom_message", "message": "Hello"},
            "test_invalid": {"action": "invalid_action"},
        }
        return config

    @pytest.fixture
    def executor(self, config):
        model_manager = ModelManager(config)
        state_manager = StateManager()
        return CommandExecutor(config, model_manager, state_manager)

    # CommandExecutor Tests - Target specific missed lines
    def test_execute_keypress_with_shim_import_error(self, executor):
        """Test keypress execution when shim import fails"""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
                mock_pg.hotkey = MagicMock()

                result = executor.execute_command("test_keypress")

                assert result is True
                mock_pg.hotkey.assert_called_once_with("ctrl", "c")

    def test_execute_keypress_pyautogui_none_error(self, executor):
        """Test keypress execution when pyautogui is None"""
        with patch("chatty_commander.app.command_executor.pyautogui", None):
            with patch("logging.error") as mock_log:
                result = executor.execute_command("test_keypress")

                assert result is False
                mock_log.assert_called()

    def test_execute_keypress_runtime_error_handling(self, executor):
        """Test keypress execution runtime error handling"""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
            mock_pg.hotkey.side_effect = RuntimeError("pyautogui not available")

            with (
                patch("logging.error") as mock_pg,
                patch("logging.critical") as mock_critical,
            ):
                result = executor.execute_command("test_keypress")

                assert result is False
                mock_critical.assert_called()

    def test_execute_url_request_exception(self, executor):
        """Test URL execution with request exception"""
        with patch(
            "requests.get", side_effect=requests.RequestException("Connection failed")
        ):
            with (
                patch("logging.error") as mock_log,
                patch("logging.critical") as mock_critical,
            ):
                result = executor.execute_command("test_url")

                assert result is False
                mock_log.assert_called()
                mock_critical.assert_called()

    def test_execute_invalid_action_type(self, executor):
        """Test execution with invalid action type"""
        with patch("logging.error") as mock_log:
            result = executor.execute_command("test_invalid")

            assert result is False
            mock_log.assert_called()

    def test_execute_nonexistent_command_error(self, executor):
        """Test execution of nonexistent command"""
        with patch("logging.error") as mock_log:
            result = executor.execute_command("nonexistent_command")

            assert result is False
            mock_log.assert_called()

    def test_report_error_logging(self, executor):
        """Test report_error method logging"""
        with patch("logging.critical") as mock_log:
            executor.report_error("test_cmd", "Test error message")

            mock_log.assert_called_once_with("Error in test_cmd: Test error message")

    def test_execute_keypress_with_list_keys(self, executor):
        """Test keypress execution with list of keys"""
        executor.config.model_actions["test_list"] = {
            "action": "keypress",
            "keys": ["ctrl", "c"],
        }

        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
            mock_pg.hotkey = MagicMock()

            result = executor.execute_command("test_list")

            assert result is True
            mock_pg.hotkey.assert_called_once_with("ctrl", "c")

    def test_execute_keypress_single_key(self, executor):
        """Test keypress execution with single key"""
        executor.config.model_actions["test_single"] = {
            "action": "keypress",
            "keys": "a",
        }

        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
            mock_pg.press = MagicMock()

            result = executor.execute_command("test_single")

            assert result is True
            mock_pg.press.assert_called_once_with("a")

    def test_execute_keypress_invalid_keys_type(self, executor):
        """Test keypress execution with invalid keys type"""
        executor.config.model_actions["test_invalid_keys"] = {
            "action": "keypress",
            "keys": 123,
        }

        with patch("chatty_commander.app.command_executor.pyautogui") as _:
            with patch("logging.error") as mock_log:
                result = executor.execute_command("test_invalid_keys")

                assert result is False
                mock_log.assert_called()

    def test_execute_url_success_logging(self, executor):
        """Test URL execution success with logging"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            with patch("logging.info") as _:
                result = executor.execute_command("test_url")

                assert result is True
                mock_get.assert_called_once_with("http://example.com", timeout=10)

    def test_execute_custom_message_logging(self, executor):
        """Test custom message execution with logging"""
        with patch("logging.info") as mock_log:
            result = executor.execute_command("test_custom")

            assert result is True
            mock_log.assert_called()

    # Voice Pipeline Tests - Basic coverage
    def test_voice_pipeline_initialization(self):
        """Test VoicePipeline initialization"""
        from chatty_commander.voice.pipeline import VoicePipeline

        pipeline = VoicePipeline()
        assert pipeline is not None

    def test_voice_pipeline_with_config(self):
        """Test VoicePipeline with config manager"""
        from chatty_commander.voice.pipeline import VoicePipeline

        mock_config = MagicMock()
        pipeline = VoicePipeline(config_manager=mock_config)
        assert pipeline is not None

    def test_voice_pipeline_with_executor(self):
        """Test VoicePipeline with command executor"""
        from chatty_commander.voice.pipeline import VoicePipeline

        mock_executor = MagicMock()
        pipeline = VoicePipeline(command_executor=mock_executor)
        assert pipeline is not None

    # Additional edge case tests
    def test_command_executor_edge_cases(self, executor):
        """Test command executor edge cases"""
        # Test empty command action
        executor.config.model_actions["empty"] = {}

        with patch("logging.error") as mock_log:
            result = executor.execute_command("empty")
            assert result is False
            mock_log.assert_called()

    # Additional coverage for missed lines in other modules
    def test_additional_coverage_scenarios(self):
        """Test additional coverage scenarios"""
        # Test Config module edge cases
        config = Config()

        # Test that config has expected attributes
        assert hasattr(config, "model_actions")
        assert hasattr(config, "inference_framework")

        # Test ModelManager initialization
        model_manager = ModelManager(config)
        assert model_manager.config == config

        # Test StateManager initialization
        state_manager = StateManager()
        assert state_manager is not None

    def test_logging_edge_cases(self):
        """Test logging edge cases"""
        from chatty_commander.utils.logger import setup_logger

        # Test logger setup with different configurations
        logger = setup_logger("test_logger")
        assert logger is not None

        # Test logger with custom config
        config = MagicMock()
        config.logging = {"level": "DEBUG", "format": "simple"}
        logger = setup_logger("test_debug", config=config)
        assert logger is not None

    def test_error_handling_edge_cases(self):
        """Test error handling edge cases"""
        from chatty_commander.utils.logger import report_error

        # Test error reporting with different error types
        error = ValueError("Test error")
        with patch("logging.error"):
            report_error(error)

        # Test error reporting with config
        config = MagicMock()
        with patch("logging.error"):
            report_error(error, config=config)


# Test 0% coverage modules
def test_switch_mode_tool():
    """Test the switch_mode tool function."""
    from chatty_commander.advisors.tools.switch_mode import switch_mode

    # Test valid mode
    result = switch_mode("idle")
    assert result == "SWITCH_MODE:idle"

    # Test empty string
    result = switch_mode("")
    assert result == "SWITCH_MODE:invalid"

    # Test whitespace
    result = switch_mode("   ")
    assert result == "SWITCH_MODE:invalid"

    # Test None
    result = switch_mode(None)
    assert result == "SWITCH_MODE:invalid"

    # Test complex mode
    result = switch_mode("voice_assistant")
    assert result == "SWITCH_MODE:voice_assistant"


def test_legacy_cli_shim():
    """Test the legacy CLI shim module."""

    from chatty_commander.cli import cli

    # Test that cli_main is available
    assert hasattr(cli, "cli_main")

    # Test that it's callable
    assert callable(cli.cli_main)


def test_legacy_command_executor_shim():
    """Test the legacy command executor shim module."""
    from chatty_commander import command_executor

    # Test that pyautogui and requests are available (may be None)
    assert hasattr(command_executor, "pyautogui")
    assert hasattr(command_executor, "requests")

    # Test that CommandExecutor is available via __getattr__
    CommandExecutor = command_executor.__getattr__("CommandExecutor")
    assert CommandExecutor is not None

    # Test that invalid attributes raise AttributeError
    with pytest.raises(AttributeError):
        command_executor.__getattr__("InvalidName")


def test_compat_module():
    """Test the compat module."""
    from chatty_commander import compat

    # Test that the module exists and can be imported
    assert compat is not None


def test_legacy_config_modules():
    """Test legacy config modules."""
    from chatty_commander import config, default_config

    # Test that modules exist and can be imported
    assert config is not None
    assert default_config is not None


# Test low coverage areas in existing modules
def test_command_executor_edge_cases():
    """Test edge cases in command executor that aren't covered."""
    from unittest.mock import MagicMock

    from chatty_commander.app.command_executor import CommandExecutor

    # Create mock dependencies
    mock_config = MagicMock()
    mock_config.model_actions = {}  # Empty actions
    mock_model_manager = MagicMock()
    mock_state_manager = MagicMock()

    executor = CommandExecutor(mock_config, mock_model_manager, mock_state_manager)
    executor.tolerant_mode = True  # Enable tolerant mode

    # Test with None command
    result = executor.execute_command(None)
    assert result is False

    # Test with empty dict
    result = executor.execute_command({})
    assert result is False

    # Test with invalid command type
    result = executor.execute_command({"invalid": "command"})
    assert result is False

    # Test keypress with missing keys
    result = executor.execute_command({"action": "keypress"})
    assert result is False

    # Test URL with missing url
    result = executor.execute_command({"action": "url"})
    assert result is False

    # Test shell with missing command
    result = executor.execute_command({"action": "shell"})
    assert result is False


def test_config_edge_cases():
    """Test edge cases in config module."""
    from unittest.mock import patch

    from chatty_commander.app.config import Config

    # Test config with invalid path
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = Config("nonexistent.yaml")
        assert config is not None

    # Test config with invalid YAML - patch json.load to avoid the mock issue
    with patch("json.load", side_effect=ValueError("Invalid JSON")):
        config = Config("invalid.yaml")
        assert config is not None


def test_cli_edge_cases():
    """Test edge cases in CLI module."""
    from unittest.mock import patch

    from chatty_commander.cli.cli import cli_main

    # Test CLI with invalid arguments
    with patch("sys.argv", ["chatty-commander", "invalid-command"]):
        # This should not crash
        try:
            cli_main()
        except SystemExit:
            pass  # Expected for invalid commands
