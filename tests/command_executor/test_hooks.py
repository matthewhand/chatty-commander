"""
Hook functionality tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch, call
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorHooks:
    """Test hook functionality."""

    def test_pre_execute_hook_sets_last_command(self, command_executor):
        """Test pre-execute hook sets last_command."""
        assert command_executor.last_command is None

        command_executor.pre_execute_hook("test_shell")

        assert command_executor.last_command == "test_shell"

    def test_pre_execute_hook_overwrites_last_command(self, command_executor):
        """Test pre-execute hook overwrites existing last_command."""
        command_executor.last_command = "previous_command"

        command_executor.pre_execute_hook("test_shell")

        assert command_executor.last_command == "test_shell"

    def test_pre_execute_hook_with_none(self, command_executor):
        """Test pre-execute hook with None command."""
        command_executor.last_command = "previous_command"

        command_executor.pre_execute_hook(None)

        assert command_executor.last_command is None

    def test_pre_execute_hook_with_empty_string(self, command_executor):
        """Test pre-execute hook with empty string."""
        command_executor.last_command = "previous_command"

        command_executor.pre_execute_hook("")

        assert command_executor.last_command == ""

    def test_pre_execute_hook_with_special_characters(self, command_executor):
        """Test pre-execute hook with special characters."""
        special_cmd = "cmd-with_special.chars123"

        command_executor.pre_execute_hook(special_cmd)

        assert command_executor.last_command == special_cmd

    def test_pre_execute_hook_called_during_execution(self, command_executor):
        """Test that pre-execute hook is called during command execution."""
        with patch.object(command_executor, "pre_execute_hook") as mock_hook:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                command_executor.execute_command("test_shell")

                mock_hook.assert_called_once_with("test_shell")

    def test_pre_execute_hook_called_before_execution(self, command_executor):
        """Test that pre-execute hook is called before actual execution."""
        call_order = []

        def mock_hook(cmd):
            call_order.append("hook")

        def mock_run(*args, **kwargs):
            call_order.append("execute")
            return Mock(returncode=0)

        with patch.object(command_executor, "pre_execute_hook", side_effect=mock_hook):
            with patch("subprocess.run", side_effect=mock_run):
                command_executor.execute_command("test_shell")

                assert call_order == ["hook", "execute"]

    def test_pre_execute_hook_with_execution_failure(self, command_executor):
        """Test pre-execute hook behavior when execution fails."""
        with patch.object(command_executor, "pre_execute_hook") as mock_hook:
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Execution failed")

                result = command_executor.execute_command("test_shell")

                mock_hook.assert_called_once_with("test_shell")
                assert result is False
                assert command_executor.last_command == "test_shell"

    def test_pre_execute_hook_with_validation_failure(self, command_executor):
        """Test pre-execute hook behavior when validation fails."""
        with patch.object(command_executor, "pre_execute_hook") as mock_hook:
            result = command_executor.execute_command("nonexistent")

            # Hook should still be called even for invalid commands
            mock_hook.assert_called_once_with("nonexistent")
            assert result is False
            assert command_executor.last_command == "nonexistent"

    def test_multiple_pre_execute_hooks(self, command_executor):
        """Test multiple consecutive pre-execute hooks."""
        commands = ["test_shell", "test_keypress", "test_url"]

        for cmd in commands:
            command_executor.pre_execute_hook(cmd)
            assert command_executor.last_command == cmd

    def test_pre_execute_hook_thread_safety(self, command_executor):
        """Test pre-execute hook behavior in concurrent scenarios."""
        import threading
        import time

        results = []

        def hook_worker(cmd):
            command_executor.pre_execute_hook(cmd)
            time.sleep(0.01)  # Small delay to simulate race condition
            results.append(command_executor.last_command)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=hook_worker, args=(f"cmd_{i}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should have set their respective commands
        assert len(results) == 5
        assert all(result.startswith("cmd_") for result in results)

    def test_pre_execute_hook_performance(self, command_executor):
        """Test pre-execute hook performance."""
        import time

        start_time = time.perf_counter()

        for i in range(1000):
            command_executor.pre_execute_hook(f"cmd_{i}")

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should complete quickly (less than 0.1 seconds for 1000 calls)
        assert duration < 0.1, f"Hook performance too slow: {duration:.3f}s"

    def test_pre_execute_hook_memory_usage(self, command_executor):
        """Test pre-execute hook doesn't cause memory leaks."""
        import sys

        initial_size = (
            sys.getsizeof(command_executor.last_command)
            if command_executor.last_command
            else 0
        )

        # Set many different commands
        for i in range(100):
            command_executor.pre_execute_hook(f"very_long_command_name_{i}" * 10)

        final_size = (
            sys.getsizeof(command_executor.last_command)
            if command_executor.last_command
            else 0
        )

        # Memory usage should be reasonable (only storing last command)
        assert final_size < 1000, f"Memory usage too high: {final_size} bytes"
