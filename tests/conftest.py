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
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager

# Ensure project root and src/ are importable so `python -m chatty_commander.main` works
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
for path in (PROJECT_ROOT, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


# ============================================================================
# SHARED TEST UTILITIES
# ============================================================================


class TestDataFactory:
    """Factory for creating consistent test data across all tests."""

    @staticmethod
    def create_valid_config_data() -> dict[str, Any]:
        """Create valid configuration data for testing."""
        return {
            "default_state": "idle",
            "general_models_path": "models-idle",
            "system_models_path": "models-computer",
            "chat_models_path": "models-chatty",
            "state_models": {
                "idle": ["model1", "model2"],
                "computer": ["model3"],
                "chatty": ["model4"],
            },
            "model_actions": {
                "test_cmd": {"action": "shell", "cmd": "echo test"},
                "keypress_cmd": {"action": "keypress", "keys": "space"},
                "url_cmd": {"action": "url", "url": "http://example.com"},
                "msg_cmd": {"action": "custom_message", "message": "Hello"},
            },
            "wakeword_state_map": {
                "hey": "computer",
                "stop": "idle",
                "hello": "chatty",
            },
            "state_transitions": {
                "idle": {"start": "computer", "chat": "chatty"},
                "computer": {"stop": "idle"},
                "chatty": {"end": "idle"},
            },
            "commands": {
                "hello": {"action": "custom_message", "message": "Hi!"},
                "screenshot": {"action": "keypress", "keys": "f12"},
            },
            "advisors": {
                "enabled": False,
                "llm_api_mode": "completion",
                "model": "gpt-4",
            },
            "voice_only": False,
            "web_server": {"host": "0.0.0.0", "port": 8000, "auth_enabled": False},
        }

    @staticmethod
    def create_mock_config(config_data: dict[str, Any] | None = None) -> Mock:
        """Create a properly configured mock Config object."""
        config = Mock(spec=Config)
        data = config_data or TestDataFactory.create_valid_config_data()
        config.config_data = data
        config.config = data
        config.default_state = data.get("default_state", "idle")
        config.save_config = Mock()
        config.reload_config = Mock(return_value=True)
        return config

    @staticmethod
    def create_mock_state_manager(config: Mock | None = None) -> Mock:
        """Create a properly configured mock StateManager."""
        sm = Mock(spec=StateManager)
        sm.current_state = "idle"
        sm.config = config or TestDataFactory.create_mock_config()
        sm.change_state = Mock(return_value=True)
        sm.process_command = Mock(return_value=True)
        sm.get_active_models = Mock(return_value=["model1", "model2"])
        sm.add_state_change_callback = Mock()
        return sm

    @staticmethod
    def create_mock_model_manager() -> Mock:
        """Create a properly configured mock ModelManager."""
        mm = Mock(spec=ModelManager)
        mm.get_models = Mock(return_value=["model1", "model2", "model3"])
        mm.reload_models = Mock(return_value=True)
        return mm

    @staticmethod
    def create_mock_command_executor(config: Mock | None = None) -> Mock:
        """Create a properly configured mock CommandExecutor."""
        ce = Mock(spec=CommandExecutor)
        ce.validate_command = Mock(return_value=True)
        ce.execute_command = Mock(return_value=True)
        ce.config = config or TestDataFactory.create_mock_config()
        ce.last_command = None
        ce.pre_execute_hook = Mock()
        return ce


# ============================================================================
# CUSTOM ASSERTION HELPERS
# ============================================================================


class TestAssertions:
    """Custom assertion helpers for better test readability and maintainability."""

    @staticmethod
    def assert_config_valid(config: Config) -> None:
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


# ============================================================================
# TEST UTILITIES
# ============================================================================


class TestUtils:
    """Utility functions for common test operations."""

    @staticmethod
    @contextmanager
    def temporary_file(
        suffix: str = ".json", content: str | None = None
    ) -> Generator[Path, None, None]:
        """Create a temporary file with optional content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            temp_path = Path(f.name)
            if content:
                f.write(content)
                f.flush()
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @staticmethod
    @contextmanager
    def temporary_directory() -> Generator[Path, None, None]:
        """Create a temporary directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_"))
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def create_test_config_file(data: dict[str, Any]) -> Path:
        """Create a test configuration file with the given data."""
        temp_file = Path(tempfile.mktemp(suffix=".json"))
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        return temp_file

    @staticmethod
    def mock_environment_variables(**kwargs) -> Mock:
        """Create a mock for environment variables."""
        mock_env = Mock()
        mock_env.get = Mock(
            side_effect=lambda key, default=None: kwargs.get(key, default)
        )
        return mock_env

    @staticmethod
    def generate_test_data(size: int, pattern: str = "test_{}") -> list[str]:
        """Generate test data following a pattern."""
        return [pattern.format(i) for i in range(size)]

    @staticmethod
    def measure_execution_time(func: callable, *args, **kwargs) -> tuple:
        """Measure the execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        return result, duration


# ============================================================================
# SHARED FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def session_temp_dir() -> Generator[Path, None, None]:
    """Provide a session-scoped temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp(prefix="chatty_test_session_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests that need file system access."""
    temp_path = Path(tempfile.mkdtemp(prefix="chatty_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Provide a temporary file for tests."""
    temp_file = temp_dir / "test_config.json"
    yield temp_file
    # File is cleaned up by temp_dir fixture


@pytest.fixture(scope="session")
def mock_config_session() -> Mock:
    """Provide a session-scoped properly configured mock Config object."""
    return TestDataFactory.create_mock_config()


@pytest.fixture
def mock_config() -> Mock:
    """Provide a properly configured mock Config object."""
    return TestDataFactory.create_mock_config()


@pytest.fixture
def mock_state_manager(mock_config: Mock) -> Mock:
    """Provide a properly configured mock StateManager."""
    return TestDataFactory.create_mock_state_manager(mock_config)


@pytest.fixture
def mock_model_manager() -> Mock:
    """Provide a properly configured mock ModelManager."""
    return TestDataFactory.create_mock_model_manager()


@pytest.fixture
def mock_command_executor(mock_config: Mock) -> Mock:
    """Provide a properly configured mock CommandExecutor."""
    return TestDataFactory.create_mock_command_executor(mock_config)


@pytest.fixture
def real_config(temp_file: Path) -> Config:
    """Provide a real Config instance for integration tests."""
    return Config(str(temp_file))


@pytest.fixture
def real_state_manager(mock_config: Mock) -> StateManager:
    """Provide a real StateManager instance."""
    return StateManager(mock_config)


@pytest.fixture(autouse=True)
def cleanup_mocks() -> Generator[None, None, None]:
    """Clean up any mocks created during tests."""
    yield
    # Reset all mocks to clean state
    from unittest.mock import _patch_stopall

    _patch_stopall()


@pytest.fixture(autouse=True)
def clear_agents_store() -> Generator[None, None, None]:
    """Clear the in-memory agent blueprint store before each test.

    Prevents test pollution from the module-level _STORE and _TEAM dicts
    that persist across tests when the agents module is imported once.
    """
    try:
        import chatty_commander.web.routes.agents as _agents_mod
        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass  # Module not yet imported or unavailable — no-op
    yield
    # Also clear after the test to leave a clean state
    try:
        import chatty_commander.web.routes.agents as _agents_mod
        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass
