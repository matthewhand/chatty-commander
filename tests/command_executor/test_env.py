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

"""
Environment-specific tests for CommandExecutor.
"""

import os
import platform
from unittest.mock import Mock, patch

import pytest


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
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            if platform_name == "Windows":
                result = command_executor.execute_command("windows_cmd")
                mock_run.assert_called_once_with(
                    ["dir"], capture_output=True, text=True, timeout=15
                )
            else:
                result = command_executor.execute_command("unix_cmd")
                mock_run.assert_called_once_with(
                    ["ls"], capture_output=True, text=True, timeout=15
                )

            assert result is True

    @patch("src.chatty_commander.app.command_executor.pyautogui.hotkey")
    def test_keypress_platform_differences(
        self, mock_hotkey, command_executor, mock_config
    ):
        """Test keypress commands across platforms."""
        # Test platform-specific key combinations
        key_combinations = [
            (["ctrl", "c"], "universal"),
            (["cmd", "c"], "mac"),
            (["ctrl", "alt", "delete"], "windows"),
        ]

        for keys, platform_name in key_combinations:
            mock_config.model_actions = {
                f"{platform_name}_keys": {"action": "keypress", "keys": keys}
            }

            result = command_executor.execute_command(f"{platform_name}_keys")
            assert result is True
            mock_hotkey.assert_called_with(*keys)

    def test_environment_variable_usage(self, command_executor, mock_config):
        """Test commands that use environment variables."""
        mock_config.model_actions = {
            "env_cmd": {"action": "shell", "cmd": "echo $HOME"}
        }

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["echo", "$HOME"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = command_executor.execute_command("env_cmd")
            assert result is True
            mock_shlex.assert_called_once_with("echo $HOME")
            mock_run.assert_called_once_with(
                ["echo", "$HOME"], capture_output=True, text=True, timeout=15
            )

    def test_path_separator_handling(self, command_executor, mock_config):
        """Test path separator handling across platforms."""
        if platform.system() == "Windows":
            path_cmd = "dir C:\\Users\\%USERNAME%"
            expected_args = ["dir", "C:\\Users\\%USERNAME%"]
        else:
            path_cmd = "ls $HOME"
            expected_args = ["ls", "$HOME"]

        mock_config.model_actions = {"path_cmd": {"action": "shell", "cmd": path_cmd}}

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = expected_args
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = command_executor.execute_command("path_cmd")
            assert result is True
            mock_shlex.assert_called_once_with(path_cmd)
            mock_run.assert_called_once_with(
                expected_args, capture_output=True, text=True, timeout=15
            )

    @patch("src.chatty_commander.app.command_executor.requests.get")
    def test_url_opening_cross_platform(self, mock_get, command_executor):
        """Test URL opening works across platforms."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = command_executor.execute_command("test_url")
        assert result is True
        mock_get.assert_called_once_with("http://example.com")

    def test_command_executor_with_missing_dependencies(
        self, command_executor, mock_config
    ):
        """Test behavior when optional dependencies are missing."""
        mock_config.model_actions = {
            "test_cmd": {"action": "shell", "cmd": "echo test"}
        }

        # Should handle missing dependencies gracefully
        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["echo", "test"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

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

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:

            def shlex_side_effect(cmd):
                if cmd == "echo development":
                    return ["echo", "development"]
                elif cmd == "echo production":
                    return ["echo", "production"]
                else:
                    return ["echo", "unknown"]

            mock_shlex.side_effect = shlex_side_effect
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            # Test dev command
            result = command_executor.execute_command("dev_cmd")
            assert result is True
            mock_run.assert_called_with(
                ["echo", "development"], capture_output=True, text=True, timeout=15
            )

            # Test prod command
            result = command_executor.execute_command("prod_cmd")
            assert result is True
            mock_run.assert_called_with(
                ["echo", "production"], capture_output=True, text=True, timeout=15
            )

    @patch.dict(os.environ, {"TEST_VAR": "test_value"})
    def test_environment_variable_expansion(self, command_executor, mock_config):
        """Test environment variable expansion in commands."""
        mock_config.model_actions = {
            "expand_cmd": {"action": "shell", "cmd": "echo $TEST_VAR"}
        }

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["echo", "$TEST_VAR"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = command_executor.execute_command("expand_cmd")
            assert result is True
            # The command should be passed as-is to subprocess
            mock_shlex.assert_called_once_with("echo $TEST_VAR")
            mock_run.assert_called_once_with(
                ["echo", "$TEST_VAR"], capture_output=True, text=True, timeout=15
            )

    def test_working_directory_handling(self, command_executor, mock_config):
        """Test commands that depend on working directory."""
        mock_config.model_actions = {"pwd_cmd": {"action": "shell", "cmd": "pwd"}}

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["pwd"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = command_executor.execute_command("pwd_cmd")
            assert result is True
            mock_shlex.assert_called_once_with("pwd")
            mock_run.assert_called_once_with(
                ["pwd"], capture_output=True, text=True, timeout=15
            )

    def test_permission_handling(self, command_executor, mock_config):
        """Test permission-related scenarios."""
        mock_config.model_actions = {
            "perm_cmd": {"action": "shell", "cmd": "echo test"}
        }

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["echo", "test"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            # Test successful execution
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

        with patch("subprocess.run") as mock_run, patch("shlex.split") as mock_shlex:
            mock_shlex.return_value = ["echo", "test with unicode: ñáéíóú"]
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = command_executor.execute_command("locale_cmd")
            assert result is True
            mock_shlex.assert_called_once_with("echo 'test with unicode: ñáéíóú'")
            mock_run.assert_called_once_with(
                ["echo", "test with unicode: ñáéíóú"],
                capture_output=True,
                text=True,
                timeout=15,
            )
