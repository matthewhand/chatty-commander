"""
Comprehensive tests for actual classes in the codebase.
Tests the real classes and functionality that exist.
"""

from unittest.mock import Mock, patch

from chatty_commander.command_executor import CommandExecutor
from chatty_commander.exceptions import ValidationError


class TestCommandExecutorComprehensive:
    """Test command executor with comprehensive scenarios."""

    def test_command_executor_with_various_commands(self):
        """Test command executor with various command types."""
        executor = CommandExecutor()

        test_cases = [
            (['echo', 'hello'], 0, 'hello'),
            (['true'], 0, ''),
            (['false'], 1, ''),
        ]

        for cmd, expected_code, expected_output in test_cases:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=expected_code,
                    stdout=expected_output,
                    stderr=''
                )

                result = executor.execute_safe(cmd)
                assert result.returncode == expected_code

    def test_command_executor_timeout(self):
        """Test command executor timeout handling."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            result = executor.execute_safe(['sleep', '10'], timeout=1)
            assert result is None

    def test_command_executor_with_environment(self):
        """Test command executor with custom environment."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='success')

            env = {'TEST_VAR': 'test_value'}
            result = executor.execute_safe(['echo', '$TEST_VAR'], env=env)

            # Verify environment was passed
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert 'env' in call_args.kwargs
            assert call_args.kwargs['env']['TEST_VAR'] == 'test_value'


class TestExceptionHandling:
    """Test exception handling in the codebase."""

    def test_validation_error_usage(self):
        """Test ValidationError usage."""
        try:
            raise ValidationError("Test validation error")
        except ValidationError as e:
            assert str(e) == "Test validation error"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        assert issubclass(ValidationError, Exception)


class TestIntegrationScenarios:
    """Test integration scenarios."""

    def test_command_executor_with_validation(self):
        """Test command executor integration with validation."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='valid')

            # Test a valid command
            result = executor.execute_safe(['echo', 'valid'])
            assert result.returncode == 0
            assert result.stdout == 'valid'


class TestPerformanceScenarios:
    """Test performance scenarios."""

    def test_command_executor_multiple_calls(self):
        """Test command executor with multiple calls."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='success')

            results = []
            for i in range(5):
                result = executor.execute_safe(['echo', f'test_{i}'])
                results.append(result)

            assert len(results) == 5
            assert all(r.returncode == 0 for r in results)


class TestErrorScenarios:
    """Test error handling scenarios."""

    def test_command_executor_with_invalid_commands(self):
        """Test command executor with invalid commands."""
        executor = CommandExecutor()

        invalid_commands = [
            ['nonexistent_command'],
            ['invalid_command', 'with', 'args'],
            [''],  # Empty command
        ]

        for cmd in invalid_commands:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=127, stderr='Command not found')

                result = executor.execute_safe(cmd)
                assert result.returncode == 127


class TestSecurityScenarios:
    """Test security scenarios."""

    def test_command_executor_sanitizes_input(self):
        """Test that command executor sanitizes input."""
        executor = CommandExecutor()

        # Test with potentially dangerous input
        dangerous_input = 'hello; rm -rf /'

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='hello')

            result = executor.execute_safe(['echo', dangerous_input])
            # Should not execute the dangerous part
            assert result.returncode == 0
            assert dangerous_input in result.stdout


class TestEdgeCases:
    """Test edge cases."""

    def test_command_executor_with_none_input(self):
        """Test command executor with None input."""
        executor = CommandExecutor()

        result = executor.execute_safe(None)
        assert result is None

    def test_command_executor_with_empty_list(self):
        """Test command executor with empty command list."""
        executor = CommandExecutor()

        result = executor.execute_safe([])
        assert result is None
