#!/usr/bin/env python3
"""
Performance benchmarking tests for ChattyCommander core modules.
These tests measure execution time and resource usage for critical operations.
"""

import os
import time
from unittest.mock import MagicMock, patch

import psutil
import pytest

# Import modules to test
try:
    from config import Config
    from model_manager import ModelManager
    from state_manager import StateManager

    from src.chatty_commander.command_executor import CommandExecutor
except ImportError:
    # Handle headless environment
    import os

    os.environ['DISPLAY'] = ':0'  # Set dummy display for headless testing
    from config import Config
    from model_manager import ModelManager
    from state_manager import StateManager

    from src.chatty_commander.command_executor import CommandExecutor


class TestPerformanceBenchmarks:
    """Performance benchmarking test suite."""

    @pytest.fixture
    def config(self):
        """Create a test config instance."""
        return Config()

    @pytest.fixture
    def state_manager(self):
        """Create a test state manager instance."""
        return StateManager()

    @pytest.fixture
    def model_manager(self, config):
        """Create a test model manager instance."""
        return ModelManager(config)

    @pytest.fixture
    def command_executor(self, config, model_manager, state_manager):
        """Create a test command executor instance."""
        return CommandExecutor(config, model_manager, state_manager)

    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage during function execution."""
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        result = func(*args, **kwargs)
        memory_after = process.memory_info().rss
        memory_delta = memory_after - memory_before
        return result, memory_delta

    def test_config_loading_performance(self, config):
        """Test configuration loading performance."""
        # Benchmark config loading
        _, execution_time = self.measure_execution_time(config._load_config)

        # Assert reasonable performance (should load in under 100ms)
        assert execution_time < 0.1, f"Config loading took {execution_time:.3f}s, expected < 0.1s"

        # Test memory usage
        _, memory_delta = self.measure_memory_usage(config._load_config)

        # Memory usage should be reasonable (less than 10MB)
        assert abs(memory_delta) < 10 * 1024 * 1024, f"Config loading used {memory_delta} bytes"

    def test_state_transition_performance(self, state_manager):
        """Test state transition performance."""
        # Benchmark state transitions
        transitions = [
            ('idle', 'chatty'),
            ('chatty', 'computer'),
            ('computer', 'idle'),
            ('idle', 'chatty'),
        ]

        total_time = 0
        for from_state, to_state in transitions:
            state_manager.current_state = from_state
            _, execution_time = self.measure_execution_time(state_manager.change_state, to_state)
            total_time += execution_time

        # All transitions should complete in under 10ms
        assert total_time < 0.01, f"State transitions took {total_time:.3f}s, expected < 0.01s"

        # Test rapid state changes
        start_time = time.perf_counter()
        for _ in range(100):
            state_manager.change_state('chatty')
            state_manager.change_state('idle')
        end_time = time.perf_counter()

        rapid_transition_time = end_time - start_time
        assert (
            rapid_transition_time < 0.1
        ), f"100 rapid transitions took {rapid_transition_time:.3f}s"

    @patch('model_manager.os.path.exists')
    @patch('model_manager.os.listdir')
    def test_model_loading_performance(self, mock_listdir, mock_exists, model_manager):
        """Test model loading performance."""
        # Mock file system for consistent testing
        mock_exists.return_value = True
        mock_listdir.return_value = ['model1.onnx', 'model2.onnx', 'model3.onnx']

        # Mock model loading to avoid actual file I/O
        with patch(
            'model_manager.Model', return_value=MagicMock()
        ) as mock_model:  # noqa: F841 - context var not used directly
            # Benchmark model loading
            _, execution_time = self.measure_execution_time(model_manager.reload_models, 'idle')

            # Model loading should be fast (under 500ms for mocked models)
            assert (
                execution_time < 0.5
            ), f"Model loading took {execution_time:.3f}s, expected < 0.5s"

    def test_command_execution_performance(self, command_executor):
        """Test command execution performance."""
        # Define test commands with the correct structure
        command_executor.config.model_actions['test_cmd_1'] = {'keypress': 'space'}
        command_executor.config.model_actions['test_cmd_2'] = {'keypress': 'enter'}
        command_executor.config.model_actions['test_cmd_3'] = {'url': 'https://example.com'}
        test_command_names = ['test_cmd_1', 'test_cmd_2', 'test_cmd_3']

        total_time = 0
        for command_name in test_command_names:
            with (
                patch.object(command_executor, '_execute_keybinding'),
                patch.object(command_executor, '_execute_url'),
            ):
                _, execution_time = self.measure_execution_time(
                    command_executor.execute_command, command_name
                )
                total_time += execution_time

        # Command execution should be fast
        assert total_time < 0.05, f"Command execution took {total_time:.3f}s, expected < 0.05s"

    def test_concurrent_operations_performance(self, config, state_manager):
        """Test performance under concurrent operations."""
        import queue
        import threading

        results = queue.Queue()

        def state_change_worker():
            """Worker function for concurrent state changes."""
            start_time = time.perf_counter()
            for i in range(10):
                state_manager.change_state('chatty' if i % 2 == 0 else 'idle')
            end_time = time.perf_counter()
            results.put(end_time - start_time)

        # Run concurrent state changes
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=state_change_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all operations completed reasonably fast
        while not results.empty():
            thread_time = results.get()
            assert thread_time < 0.1, f"Concurrent operations took {thread_time:.3f}s per thread"

    def test_memory_leak_detection(self, config):
        """Test for memory leaks during repeated operations."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform repeated operations
        for _ in range(100):
            config._load_config()
            config.validate()

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal (less than 5MB)
        assert (
            memory_growth < 5 * 1024 * 1024
        ), f"Memory grew by {memory_growth} bytes after 100 operations"

    def test_startup_performance(self):
        """Test overall system startup performance."""
        start_time = time.perf_counter()

        # Simulate system startup
        config = Config()
        config._load_config()
        state_manager = StateManager()

        with (
            patch('model_manager.os.path.exists', return_value=True),
            patch('model_manager.os.listdir', return_value=['test.onnx']),
        ):
            model_manager = ModelManager(config)

        command_executor = CommandExecutor(
            config, model_manager, state_manager
        )  # noqa: F841 - constructed to validate init path; not used further in timing

        end_time = time.perf_counter()
        startup_time = end_time - start_time

        # System should start up quickly (under 1 second)
        assert startup_time < 1.0, f"System startup took {startup_time:.3f}s, expected < 1.0s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
