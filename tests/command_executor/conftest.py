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
Pytest fixtures for command_executor tests.
"""

from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.app.command_executor import CommandExecutor
from src.chatty_commander.app.config import Config
from src.chatty_commander.app.model_manager import ModelManager
from src.chatty_commander.app.state_manager import StateManager


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.model_actions = {
        "test_shell": {"action": "shell", "cmd": "echo test"},
        "test_keypress": {"action": "keypress", "keys": "space"},
        "test_url": {"action": "url", "url": "http://example.com"},
        "test_message": {"action": "custom_message", "message": "Hello World"},
    }
    return config


@pytest.fixture
def mock_subprocess_result():
    """Create a mock subprocess result with proper attributes."""
    result = Mock()
    result.returncode = 0
    result.stdout = "test output"
    result.stderr = ""
    return result


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager for testing."""
    return Mock(spec=ModelManager)


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    return Mock(spec=StateManager)


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock optional dependencies for all tests."""
    with (
        patch("src.chatty_commander.app.command_executor.pyautogui") as mock_pg,
        patch("src.chatty_commander.app.command_executor.requests") as mock_requests,
    ):
        mock_pg.press = Mock()
        mock_pg.hotkey = Mock()
        mock_requests.get = Mock()
        yield mock_pg, mock_requests


@pytest.fixture
def command_executor(mock_config, mock_model_manager, mock_state_manager):
    """Create a CommandExecutor instance with mocked dependencies."""
    return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)
