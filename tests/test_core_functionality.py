"""
Focused tests for core functionality that exists in the codebase.
Tests command_executor, config, and other core modules that have actual classes.
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.command_executor import CommandExecutor


class TestCommandExecutorReal:
    """Test real command executor functionality that exists."""

    def test_command_executor_initialization(self):
        """Test command executor initialization."""
        executor = CommandExecutor()
        assert executor is not None

    def test_safe_command_execution(self):
        """Test safe command execution."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='Success')

            result = executor.execute_safe(['echo', 'test'])
            assert result.returncode == 0

    def test_dangerous_command_blocking(self):
        """Test dangerous command blocking."""
        executor = CommandExecutor()

        dangerous_commands = [
            ['rm', '-rf', '/'],
            ['> /dev/null; rm -rf /']
        ]

        for cmd in dangerous_commands:
            result = executor.execute_safe(cmd)
            # Should be blocked or return error
            assert result is None or result.returncode != 0


class TestCoreComponents:
    """Test core components that exist."""

    def test_imports(self):
        """Test that key modules can be imported."""
        try:
            from chatty_commander import command_executor, config, helpers, utils
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestToolFunctions:
    """Test tool functions that exist."""

    def test_bridge_nodejs_functions(self):
        """Test NodeJS bridge functions."""
        try:
            from chatty_commander.tools.bridge_nodejs import generate_package_json
            result = generate_package_json()
            assert isinstance(result, str)
            assert 'chatty-commander-bridge' in result
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestWebComponents:
    """Test web components that exist."""

    def test_auth_middleware(self):
        """Test auth middleware that exists."""
        try:
            from chatty_commander.web.middleware.auth import AuthMiddleware
            middleware = AuthMiddleware()
            assert middleware is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestProviderComponents:
    """Test provider components that exist."""

    def test_ollama_provider(self):
        """Test Ollama provider that exists."""
        try:
            from chatty_commander.providers.ollama_provider import OllamaProvider
            provider = OllamaProvider()
            assert provider is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
