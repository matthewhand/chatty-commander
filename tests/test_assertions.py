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

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.state_manager import StateManager


class TestAssertions:
    """Custom assertion helpers for better test readability and maintainability."""

    @staticmethod
    def assert_config_valid(config: Any) -> None:
        """Assert that a Config object is properly initialized."""
        assert hasattr(
            config, "config_data"
        ), "Config should have config_data attribute"
        assert hasattr(config, "config"), "Config should have config attribute"
        assert isinstance(
            config.config_data, dict
        ), "config_data should be a dictionary"
        assert (
            config.config is config.config_data
        ), "config should reference config_data"

    @staticmethod
    def assert_mock_called_once_with(mock_obj: Mock, *args, **kwargs) -> None:
        """Assert that a mock was called exactly once with specific arguments."""
        mock_obj.assert_called_once()
        if args or kwargs:
            call_args = mock_obj.call_args
            if call_args:
                call_args, call_kwargs = call_args
                if args:
                    assert (
                        call_args == args
                    ), f"Expected call args {args}, got {call_args}"
                if kwargs:
                    assert (
                        call_kwargs == kwargs
                    ), f"Expected call kwargs {kwargs}, got {call_kwargs}"

    @staticmethod
    def assert_performance_within_limit(duration: float, limit_seconds: float) -> None:
        """Assert that an operation completed within the specified time limit."""
        assert (
            duration < limit_seconds
        ), f"Operation too slow: {duration:.3f}s (limit: {limit_seconds}s)"

    @staticmethod
    def assert_no_unexpected_exceptions(func: callable, *args, **kwargs) -> Any:
        """Assert that a function executes without unexpected exceptions."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @staticmethod
    def assert_file_contains_json(
        file_path: Path, expected_data: dict[str, Any]
    ) -> None:
        """Assert that a file contains the expected JSON data."""
        assert file_path.exists(), f"File {file_path} should exist"
        with open(file_path) as f:
            actual_data = json.load(f)
        assert (
            actual_data == expected_data
        ), f"File content mismatch. Expected: {expected_data}, Got: {actual_data}"

    @staticmethod
    def assert_state_manager_properly_initialized(sm: StateManager) -> None:
        """Assert that a StateManager is properly initialized."""
        assert hasattr(sm, "current_state"), "StateManager should have current_state"
        assert hasattr(sm, "config"), "StateManager should have config"
        assert sm.current_state is not None, "current_state should not be None"

    @staticmethod
    def assert_command_executor_actions_valid(ce: CommandExecutor) -> None:
        """Assert that a CommandExecutor has valid action configurations."""
        assert hasattr(ce, "config"), "CommandExecutor should have config"
        if hasattr(ce.config, "model_actions"):
            actions = ce.config.model_actions
            if actions:
                for action_name, action_config in actions.items():
                    assert isinstance(
                        action_config, dict
                    ), f"Action {action_name} should be a dict"
                    assert (
                        "action" in action_config
                    ), f"Action {action_name} should have 'action' key"
