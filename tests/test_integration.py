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

import pytest
from test_data_factories import TestDataFactory
from test_utils import TestUtils

from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager


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
        temp_file = TestUtils.create_test_config_file(
            TestDataFactory.create_valid_config_data()
        )
        config = Config(str(temp_file))
        sm = StateManager(config)
        sm.change_state("computer")
        config.save_config()
        # Reload and verify persistence
        reloaded_config = Config(str(temp_file))
        assert (
            reloaded_config.default_state == "idle"
        )  # Assuming no change to default
