import os
import shutil
import sys
import tempfile
from collections.abc import Generator
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
        base_data = TestDataFactory.create_valid_config_data()
        if config_data:
            base_data.update(config_data)
        data = base_data
        config.config_data = data
        config.config = data
        # Set all required attributes that StateManager and other components expect
        config.default_state = data.get("default_state", "idle")
        config.model_actions = data.get("model_actions", {})
        config.state_models = data.get(
            "state_models",
            {
                "idle": ["model1", "model2"],
                "computer": ["model3"],
                "chatty": ["model4"],
            },
        )
        config.wakeword_state_map = data.get("wakeword_state_map", {})
        config.state_transitions = data.get("state_transitions", {})
        config.general_models_path = data.get("general_models_path", "models-idle")
        config.system_models_path = data.get("system_models_path", "models-computer")
        config.chat_models_path = data.get("chat_models_path", "models-chatty")
        config.commands = data.get("commands", {})
        config.advisors = data.get("advisors", {"enabled": False})
        config.debug_mode = data.get("debug_mode", False)
        config.web_server = data.get(
            "web_server", {"host": "0.0.0.0", "port": 8000, "auth_enabled": False}
        )
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
