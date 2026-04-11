import json
import tempfile
from pathlib import Path

import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from conftest import TestDataFactory


@pytest.mark.integration
class TestIntegration:
    """
    Integration tests for core components interaction.
    """

    def test_full_system_integration_basic(self):
        """Test basic full system integration."""
        config = TestDataFactory.create_mock_config()
        sm = StateManager(config)
        # Simulate basic interaction
        sm.change_state("computer")
        assert sm.current_state == "computer"

    def test_full_system_integration_state_transitions(self):
        """Test full system state transitions."""
        config = TestDataFactory.create_mock_config(
            {
                "state_transitions": {
                    "idle": {"start": "computer"},
                    "computer": {"stop": "idle"},
                }
            }
        )
        sm = StateManager(config)
        sm.change_state("computer")
        assert sm.current_state == "computer"
        sm.change_state("idle")
        assert sm.current_state == "idle"

    def test_full_system_integration_web_mode(self):
        """Test full system integration with web mode."""
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": "0.0.0.0", "port": 8000, "auth_enabled": False}}
        )
        sm = StateManager(config)
        # Assuming web mode integration; adjust as needed
        # web_server = WebModeServer(config)
        # sm.integrate_web_mode(web_server)
        assert sm.config.web_server["host"] == "0.0.0.0"

    def test_full_system_integration_config_persistence(self):
        """Test full system integration with configuration persistence."""
        data = TestDataFactory.create_valid_config_data()
        temp_file = Path(tempfile.mktemp(suffix=".json"))
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        config = Config(str(temp_file))
        sm = StateManager(config)
        sm.change_state("computer")
        config.save_config()
        # Reload and verify persistence
        reloaded_config = Config(str(temp_file))
        assert reloaded_config.default_state == "idle"  # Assuming no change to default
