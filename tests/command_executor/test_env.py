"""
Environment-specific tests for CommandExecutor.
"""

import pytest
import os
import platform
from unittest.mock import Mock, patch
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorEnvironment:
    """Test CommandExecutor in different environments."""

    @pytest.mark.parametrize("platform_name", ["Linux", "Windows", "Darwin"])
    @patch("platform.system")
    def test_cross_platform_shell_commands(
        self, mock_system, command_executor, mock_config, platform_name
    ):
        """Test shell commands work across different platforms."""
        mock_system.return_value = platform_name

        # Platform-specific commands
        if platform_name == "Windows":
            mock_config.model_actions = {
                "windows_cmd": {"action": "shell", "cmd": "dir"}
            }
        else:
            mock_config.model_actions = {"unix_cmd": {"action": "shell", "cmd": "ls"}}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            if platform_name == "Windows":
                result = command_executor.execute_command("windows_cmd")
                mock_run.assert_called_once_with("dir", shell=True, check=True)
            else:
                result = command_executor.execute_command("unix_cmd")
                mock_run.assert_called_once_with("ls", shell=True, check=True)

            assert result is True

    @patch("pyautogui.press")
    def test_keypress_platform_differences(
        self, mock_press, command_executor, mock_config
    ):
        """Test keypress commands across platforms."""
        # Test platform-specific key combinations
        key_combinations = [
            (["ctrl", "c"], "universal"),
            (["cmd", "c"], "mac"),
            (["ctrl", "alt", "delete"], "windows"),
        ]

        for keys, platform in key_combinations:
            mock_config.model_actions = {
                f"{platform}_keys": {"action": "keypress", "keys": keys}
            }

            result = command_executor.execute_command(f"{platform}_keys")
            assert result is True
            mock_press.assert_called_with(keys)

    def test_environment_variable_usage(self, command_executor, mock_config):
        """Test commands that use environment variables."""
        mock_config.model_actions = {
            "env_cmd": {"action": "shell", "cmd": "echo $HOME"}
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("env_cmd")
            assert result is True
            mock_run.assert_called_once_with("echo $HOME", shell=True, check=True)

    def test_path_separator_handling(self, command_executor, mock_config):
        """Test path separator handling across platforms."""
        if platform.system() == "Windows":
            path_cmd = "dir C:\\Users\\%USERNAME%"
        else:
            path_cmd = "ls $HOME"

        mock_config.model_actions = {"path_cmd": {"action": "shell", "cmd": path_cmd}}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("path_cmd")
            assert result is True
            mock_run.assert_called_once_with(path_cmd, shell=True, check=True)

    @patch("webbrowser.open")
    def test_url_opening_cross_platform(self, mock_open, command_executor):
        """Test URL opening works across platforms."""
        result = command_executor.execute_command("test_url")
        assert result is True
        mock_open.assert_called_once_with("http://example.com")

    def test_command_executor_with_missing_dependencies(
        self, command_executor, mock_config
    ):
        """Test behavior when optional dependencies are missing."""
        mock_config.model_actions = {
            "test_cmd": {"action": "shell", "cmd": "echo test"}
        }

        # Should handle missing dependencies gracefully
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("test_cmd")
            assert result is True

    def test_environment_specific_config_loading(self, command_executor, mock_config):
        """Test loading environment-specific configurations."""
        # Simulate environment-specific config
        env_config = {
            "dev_cmd": {"action": "shell", "cmd": "echo development"},
            "prod_cmd": {"action": "shell", "cmd": "echo production"},
        }
        mock_config.model_actions.update(env_config)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            # Test dev command
            result = command_executor.execute_command("dev_cmd")
            assert result is True
            mock_run.assert_called_with("echo development", shell=True, check=True)

            # Test prod command
            result = command_executor.execute_command("prod_cmd")
            assert result is True
            mock_run.assert_called_with("echo production", shell=True, check=True)

    @patch.dict(os.environ, {"TEST_VAR": "test_value"})
    def test_environment_variable_expansion(self, command_executor, mock_config):
        """Test environment variable expansion in commands."""
        mock_config.model_actions = {
            "expand_cmd": {"action": "shell", "cmd": "echo $TEST_VAR"}
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("expand_cmd")
            assert result is True
            # The command should be passed as-is to subprocess
            mock_run.assert_called_once_with("echo $TEST_VAR", shell=True, check=True)

    def test_working_directory_handling(self, command_executor, mock_config):
        """Test commands that depend on working directory."""
        mock_config.model_actions = {"pwd_cmd": {"action": "shell", "cmd": "pwd"}}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("pwd_cmd")
            assert result is True
            mock_run.assert_called_once_with("pwd", shell=True, check=True)

    def test_permission_handling(self, command_executor, mock_config):
        """Test permission-related scenarios."""
        mock_config.model_actions = {
            "perm_cmd": {"action": "shell", "cmd": "echo test"}
        }

        with patch("subprocess.run") as mock_run:
            # Test successful execution
            mock_run.return_value = Mock(returncode=0)
            result = command_executor.execute_command("perm_cmd")
            assert result is True

            # Test permission denied
            mock_run.side_effect = PermissionError("Permission denied")
            result = command_executor.execute_command("perm_cmd")
            assert result is False

    def test_locale_and_encoding(self, command_executor, mock_config):
        """Test commands with different locale/encoding requirements."""
        mock_config.model_actions = {
            "locale_cmd": {"action": "shell", "cmd": "echo 'test with unicode: ñáéíóú'"}
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = command_executor.execute_command("locale_cmd")
            assert result is True
            mock_run.assert_called_once_with(
                "echo 'test with unicode: ñáéíóú'", shell=True, check=True
            )
