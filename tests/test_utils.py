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
Test utilities and helpers for ChattyCommander testing.

This module provides shared utilities for testing including:
- Mock creation helpers
- Test data generation
- Assertion helpers
- Test isolation utilities
"""

import asyncio
import contextlib
import io
import json
import os
import sys
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager

# ============================================================================
# MOCKING HELPERS
# ============================================================================


class MockFactory:
    """Factory for creating properly configured mock objects."""

    @staticmethod
    def create_config_mock(**overrides) -> Mock:
        """Create a mock Config with sensible defaults."""
        config = Mock(spec=Config)
        defaults = {
            "config_data": {},
            "config": {},
            "default_state": "idle",
            "voice_only": False,
            "save_config": Mock(),
            "reload_config": Mock(return_value=True),
        }
        defaults.update(overrides)

        for attr, value in defaults.items():
            setattr(config, attr, value)

        return config

    @staticmethod
    def create_state_manager_mock(**overrides) -> Mock:
        """Create a mock StateManager with sensible defaults."""
        sm = Mock(spec=StateManager)
        defaults = {
            "current_state": "idle",
            "change_state": Mock(return_value=True),
            "process_command": Mock(return_value=True),
            "get_active_models": Mock(return_value=["model1", "model2"]),
            "add_state_change_callback": Mock(),
        }
        defaults.update(overrides)

        for attr, value in defaults.items():
            setattr(sm, attr, value)

        return sm

    @staticmethod
    def create_model_manager_mock(**overrides) -> Mock:
        """Create a mock ModelManager with sensible defaults."""
        mm = Mock(spec=ModelManager)
        defaults = {
            "get_models": Mock(return_value=["model1", "model2", "model3"]),
            "reload_models": Mock(return_value=True),
        }
        defaults.update(overrides)

        for attr, value in defaults.items():
            setattr(mm, attr, value)

        return mm

    @staticmethod
    def create_command_executor_mock(**overrides) -> Mock:
        """Create a mock CommandExecutor with sensible defaults."""
        ce = Mock(spec=CommandExecutor)
        defaults = {
            "validate_command": Mock(return_value=True),
            "execute_command": Mock(return_value=True),
            "last_command": None,
            "pre_execute_hook": Mock(),
            "post_execute_hook": Mock(),
        }
        defaults.update(overrides)

        for attr, value in defaults.items():
            setattr(ce, attr, value)

        return ce


# ============================================================================
# TEST ISOLATION HELPERS
# ============================================================================


class IsolationUtils:
    """Utilities for isolating tests from external dependencies."""

    @staticmethod
    @contextlib.contextmanager
    def isolated_filesystem():
        """Context manager that provides an isolated temporary filesystem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                yield Path(tmpdir)
            finally:
                os.chdir(original_cwd)

    @staticmethod
    @contextlib.contextmanager
    def captured_output():
        """Context manager that captures stdout and stderr."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            yield stdout_capture, stderr_capture
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    @staticmethod
    @contextlib.contextmanager
    def mock_environment(**env_vars):
        """Context manager that temporarily sets environment variables."""
        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)

        try:
            for key, value in env_vars.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = str(value)
            yield
        finally:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


# ============================================================================
# ASYNC TESTING HELPERS
# ============================================================================


class AsyncTestUtils:
    """Utilities for testing async code."""

    @staticmethod
    async def wait_for_condition(
        condition_func, timeout: float = 5.0, interval: float = 0.1
    ):
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)
        return False

    @staticmethod
    def run_async(coro):
        """Run an async coroutine in a test environment."""
        return asyncio.run(coro)

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create a mock that can be used as an async function."""

        async def async_mock(*args, **kwargs):
            if side_effect:
                if callable(side_effect):
                    return side_effect(*args, **kwargs)
                else:
                    raise side_effect
            return return_value

        mock = Mock(side_effect=async_mock)
        mock.return_value = return_value
        return mock


# ============================================================================
# ASSERTION HELPERS
# ============================================================================


class EnhancedAssertions:
    """Enhanced assertion helpers for better test diagnostics."""

    @staticmethod
    def assert_dict_contains_subset(subset: dict, superset: dict, msg: str = None):
        """Assert that one dict is a subset of another."""
        missing_keys = []
        different_values = []

        for key, expected_value in subset.items():
            if key not in superset:
                missing_keys.append(key)
            elif superset[key] != expected_value:
                different_values.append((key, expected_value, superset[key]))

        if missing_keys or different_values:
            error_msg = []
            if missing_keys:
                error_msg.append(f"Missing keys: {missing_keys}")
            if different_values:
                error_msg.append(f"Different values: {different_values}")
            full_msg = msg or "; ".join(error_msg)
            pytest.fail(full_msg)

    @staticmethod
    def assert_file_contains_text(file_path: Path, text: str, msg: str = None):
        """Assert that a file contains specific text."""
        assert file_path.exists(), f"File {file_path} does not exist"

        content = file_path.read_text()
        assert text in content, msg or f"Text '{text}' not found in {file_path}"

    @staticmethod
    def assert_json_files_equal(file1: Path, file2: Path, msg: str = None):
        """Assert that two JSON files contain the same data."""
        assert file1.exists(), f"File {file1} does not exist"
        assert file2.exists(), f"File {file2} does not exist"

        with open(file1) as f1, open(file2) as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        assert data1 == data2, msg or f"JSON files differ: {file1} vs {file2}"

    @staticmethod
    def assert_no_exceptions(func, *args, **kwargs):
        """Assert that a function runs without raising exceptions."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @staticmethod
    def assert_performance_acceptable(
        duration: float, max_duration: float, operation: str = "operation"
    ):
        """Assert that an operation completed within acceptable time."""
        assert (
            duration <= max_duration
        ), f"{operation} took {duration:.3f}s, exceeding limit of {max_duration:.3f}s"


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================


class TestDataGenerator:
    """Generators for various types of test data."""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string of specified length."""
        import random
        import string

        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_config_data() -> dict[str, Any]:
        """Generate random but valid config data."""
        return {
            "default_state": "idle",
            "voice_only": False,
            "commands": {
                TestDataGenerator.random_string(5): {
                    "action": "custom_message",
                    "message": TestDataGenerator.random_string(20),
                }
            },
        }

    @staticmethod
    def large_config_data(size: int = 1000) -> dict[str, Any]:
        """Generate large config data for performance testing."""
        return {f"key_{i}": f"value_{i}" for i in range(size)}


# ============================================================================
# INTEGRATION TEST HELPERS
# ============================================================================


class IntegrationTestUtils:
    """Utilities specifically for integration testing."""

    @staticmethod
    @contextlib.contextmanager
    def temp_config_file(config_data: dict[str, Any]) -> Generator[Path, None, None]:
        """Context manager that creates a temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            yield config_path
        finally:
            config_path.unlink(missing_ok=True)

    @staticmethod
    def create_test_app(
        config_data: dict[str, Any] | None = None,
    ) -> tuple[Config, StateManager, ModelManager, CommandExecutor]:
        """Create a complete test application with all components."""
        config_data = config_data or TestDataGenerator.random_config_data()

        with IntegrationTestUtils.temp_config_file(config_data) as config_path:
            config = Config(str(config_path))
            state_manager = StateManager()
            model_manager = ModelManager(config)
            command_executor = CommandExecutor(config, model_manager, state_manager)

            return config, state_manager, model_manager, command_executor
