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

import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from tests.test_1337_ultimate_coverage import TestAssertions, TestUtils


@pytest.mark.performance
class TestPerformance:
    """
    Performance tests for the ChattyCommander application.
    """

    def test_config_performance_large_config(self, temp_file: Path) -> None:
        """
        Test Config performance with large configuration data.
        Benchmarks Config operations with large datasets to ensure
        performance remains acceptable under load.
        """
        config = Config(str(temp_file))
        large_data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        config.config_data = large_data
        _, duration = TestUtils.measure_execution_time(config.save_config)
        TestAssertions.assert_performance_within_limit(duration, 1.0)
        new_config = Config(str(temp_file))
        assert len(new_config.config_data) == 1000
        assert new_config.config_data["key_999"] == "value_999"
        TestAssertions.assert_file_contains_json(temp_file, large_data)

    def test_state_manager_performance_multiple_transitions(self):
        """Test StateManager performance with multiple state transitions."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {"idle": [], "computer": [], "chatty": []}
        state_manager = StateManager(config)
        start_time = time.time()
        for _ in range(100):
            state_manager.change_state("computer")
            state_manager.change_state("idle")
        end_time = time.time()
        assert end_time - start_time < 0.5

    def test_command_executor_performance_batch_commands(self):
        """Test CommandExecutor performance with batch command execution."""
        config = Mock()
        config.model_actions = {
            f"cmd_{i}": {"action": "custom_message", "message": f"Message {i}"}
            for i in range(100)
        }
        executor = CommandExecutor(config, Mock(), Mock())
        start_time = time.time()
        for i in range(100):
            executor.execute_command(f"cmd_{i}")
        end_time = time.time()
        assert end_time - start_time < 1.0
