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
Comprehensive tests for exceptions and helper modules.

Tests exception hierarchy, inheritance, and utility functions with edge cases.
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from chatty_commander.exceptions import (
    ChattyCommanderError,
    ConfigurationError,
    DependencyError,
    ExecutionError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and inheritance."""

    def test_base_exception_inheritance(self):
        """Test that all exceptions inherit from base exception."""
        # Test direct inheritance
        assert issubclass(ConfigurationError, ChattyCommanderError)
        assert issubclass(ValidationError, ChattyCommanderError)
        assert issubclass(ExecutionError, ChattyCommanderError)
        assert issubclass(DependencyError, ChattyCommanderError)

        # Test multiple inheritance
        assert issubclass(ConfigurationError, ValueError)
        assert issubclass(ValidationError, ValueError)
        assert issubclass(ExecutionError, Exception)
        assert issubclass(DependencyError, ImportError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        # Test with message
        exc = ChattyCommanderError("Test error")
        assert str(exc) == "Test error"
        assert exc.args == ("Test error",)

        # Test without message
        exc = ChattyCommanderError()
        assert str(exc) == ""
        assert exc.args == ()

    def test_configuration_error_instantiation(self):
        """Test ConfigurationError instantiation."""
        exc = ConfigurationError("Config validation failed")
        assert str(exc) == "Config validation failed"
        assert isinstance(exc, ValueError)
        assert isinstance(exc, ChattyCommanderError)

    def test_validation_error_instantiation(self):
        """Test ValidationError instantiation."""
        exc = ValidationError("Invalid input data")
        assert str(exc) == "Invalid input data"
        assert isinstance(exc, ValueError)
        assert isinstance(exc, ChattyCommanderError)

    def test_execution_error_instantiation(self):
        """Test ExecutionError instantiation."""
        exc = ExecutionError("Command execution failed")
        assert str(exc) == "Command execution failed"
        assert isinstance(exc, Exception)
        assert isinstance(exc, ChattyCommanderError)

    def test_dependency_error_instantiation(self):
        """Test DependencyError instantiation."""
        exc = DependencyError("Missing required library")
        assert str(exc) == "Missing required library"
        assert isinstance(exc, ImportError)
        assert isinstance(exc, ChattyCommanderError)

    def test_exception_with_extra_args(self):
        """Test exceptions with additional arguments."""
        exc = ChattyCommanderError("Error", "extra", "args")
        assert str(exc) == "Error"
        assert exc.args == ("Error", "extra", "args")

    def test_exception_chaining(self):
        """Test exception chaining with __cause__ and __context__."""
        original_exc = ValueError("Original error")

        try:
            raise original_exc
        except ValueError as e:
            chained_exc = ChattyCommanderError("Chained error")
            chained_exc.__cause__ = e

            assert chained_exc.__cause__ is original_exc
            assert isinstance(chained_exc.__cause__, ValueError)

    def test_exception_context_manager(self):
        """Test exceptions work properly with context managers."""
        caught_exc = None

        try:
            with open("/nonexistent/file") as f:
                content = f.read()
        except Exception as e:
            # This should work with any exception type
            assert isinstance(e, Exception)

    def test_exception_inheritance_chain(self):
        """Test the complete inheritance chain."""
        # Test that subclasses maintain proper inheritance
        config_exc = ConfigurationError("test")
        assert isinstance(config_exc, ConfigurationError)
        assert isinstance(config_exc, ChattyCommanderError)
        assert isinstance(config_exc, ValueError)
        assert isinstance(config_exc, Exception)

        # Test MRO (Method Resolution Order)
        mro = ConfigurationError.__mro__
        expected_order = [ConfigurationError, ChattyCommanderError, ValueError, Exception, BaseException, object]
        assert mro == expected_order

    def test_exception_attributes(self):
        """Test exception attributes and properties."""
        exc = ChattyCommanderError("Test message")

        # Test basic attributes
        assert hasattr(exc, 'args')
        assert exc.args == ("Test message",)

        # Test that exceptions have proper string representation
        assert str(exc) == "Test message"
        assert repr(exc) == "ChattyCommanderError('Test message',)"

    def test_exception_equality(self):
        """Test exception equality and identity."""
        exc1 = ChattyCommanderError("Same message")
        exc2 = ChattyCommanderError("Same message")
        exc3 = ChattyCommanderError("Different message")

        # Test identity (should be different objects)
        assert exc1 is not exc2

        # Test equality based on args
        assert exc1.args == exc2.args
        assert exc1.args != exc3.args

    def test_exception_hashability(self):
        """Test that exceptions can be hashed (for use in sets/dicts)."""
        exc = ChattyCommanderError("Test")
        hash_value = hash(exc)
        assert isinstance(hash_value, int)

        # Hash should be consistent
        assert hash(exc) == hash_value

    def test_exception_pickle_support(self):
        """Test that exceptions can be pickled (for serialization)."""
        import pickle

        exc = ChattyCommanderError("Pickle test")

        # Should be able to pickle and unpickle
        pickled = pickle.dumps(exc)
        unpickled = pickle.loads(pickled)

        assert isinstance(unpickled, ChattyCommanderError)
        assert str(unpickled) == "Pickle test"

    def test_nested_exception_messages(self):
        """Test exception messages with nested formatting."""
        inner_exc = ValueError("Inner error")
        outer_exc = ChattyCommanderError(f"Outer error: {inner_exc}")

        assert "Outer error" in str(outer_exc)
        assert "Inner error" in str(outer_exc)

    def test_exception_docstrings(self):
        """Test that all exceptions have proper docstrings."""
        assert ChattyCommanderError.__doc__ is not None
        assert ConfigurationError.__doc__ is not None
        assert ValidationError.__doc__ is not None
        assert ExecutionError.__doc__ is not None
        assert DependencyError.__doc__ is not None

        # Check that docstrings contain meaningful information
        assert "Base exception" in ChattyCommanderError.__doc__
        assert "Configuration" in ConfigurationError.__doc__
        assert "Validation" in ValidationError.__doc__
        assert "Execution" in ExecutionError.__doc__
        assert "Dependency" in DependencyError.__doc__


class TestExceptionUsageScenarios:
    """Test exception usage in realistic scenarios."""

    def test_configuration_error_scenario(self):
        """Test ConfigurationError in configuration loading scenario."""
        def load_config(config_path):
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Config file not found: {config_path}")
            if not os.access(config_path, os.R_OK):
                raise ConfigurationError(f"Config file not readable: {config_path}")
            # Simulate config parsing error
            raise ConfigurationError("Invalid JSON format in config file")

        # Test file not found
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("/nonexistent/config.json")
        assert "not found" in str(exc_info.value)

        # Test permission error
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("/root/config.json")
        assert "not readable" in str(exc_info.value)

    def test_validation_error_scenario(self):
        """Test ValidationError in data validation scenario."""
        def validate_user_data(data):
            if not isinstance(data, dict):
                raise ValidationError("Data must be a dictionary")
            if "username" not in data:
                raise ValidationError("Username is required")
            if len(data["username"]) < 3:
                raise ValidationError("Username must be at least 3 characters")
            return True

        # Test invalid type
        with pytest.raises(ValidationError) as exc_info:
            validate_user_data("not_a_dict")
        assert "must be a dictionary" in str(exc_info.value)

        # Test missing field
        with pytest.raises(ValidationError) as exc_info:
            validate_user_data({})
        assert "Username is required" in str(exc_info.value)

        # Test invalid length
        with pytest.raises(ValidationError) as exc_info:
            validate_user_data({"username": "ab"})
        assert "at least 3 characters" in str(exc_info.value)

    def test_execution_error_scenario(self):
        """Test ExecutionError in command execution scenario."""
        def execute_shell_command(command):
            if command == "invalid_command":
                raise ExecutionError("Command not found: invalid_command")
            if command == "permission_denied":
                raise ExecutionError("Permission denied executing command")
            return "success"

        # Test command not found
        with pytest.raises(ExecutionError) as exc_info:
            execute_shell_command("invalid_command")
        assert "not found" in str(exc_info.value)

        # Test permission error
        with pytest.raises(ExecutionError) as exc_info:
            execute_shell_command("permission_denied")
        assert "Permission denied" in str(exc_info.value)

    def test_dependency_error_scenario(self):
        """Test DependencyError in dependency checking scenario."""
        def check_dependencies():
            try:
                import nonexistent_module
            except ImportError:
                raise DependencyError("Required module 'nonexistent_module' is not installed")

            try:
                import requests
            except ImportError:
                raise DependencyError("Optional module 'requests' is not available")

        # Test missing required dependency
        with pytest.raises(DependencyError) as exc_info:
            check_dependencies()
        assert "nonexistent_module" in str(exc_info.value)
        assert "not installed" in str(exc_info.value)

    def test_exception_catching_hierarchy(self):
        """Test catching exceptions at different levels of hierarchy."""
        caught_exceptions = []

        def test_scenario():
            try:
                raise ValidationError("Specific validation error")
            except ChattyCommanderError:
                caught_exceptions.append("ChattyCommanderError")
            except Exception:
                caught_exceptions.append("Exception")

            try:
                raise ConfigurationError("Specific config error")
            except ValueError:
                caught_exceptions.append("ValueError")
            except ChattyCommanderError:
                caught_exceptions.append("ChattyCommanderError")

            try:
                raise ChattyCommanderError("Base error")
            except Exception:
                caught_exceptions.append("Exception")

        test_scenario()

        assert "ChattyCommanderError" in caught_exceptions
        assert "ValueError" in caught_exceptions
        assert "Exception" in caught_exceptions

    def test_exception_inheritance_checking(self):
        """Test isinstance checks for exception hierarchy."""
        exc = ValidationError("test")

        assert isinstance(exc, ValidationError)
        assert isinstance(exc, ChattyCommanderError)
        assert isinstance(exc, ValueError)
        assert isinstance(exc, Exception)
        assert isinstance(exc, BaseException)

        assert not isinstance(exc, ConfigurationError)
        assert not isinstance(exc, ExecutionError)

    def test_exception_multiple_inheritance_behavior(self):
        """Test that multiple inheritance works correctly."""
        config_exc = ConfigurationError("test")

        # Should be caught by both parent exception types
        try:
            raise config_exc
        except ValueError:
            assert True  # Should be caught by ValueError
        except ChattyCommanderError:
            assert False  # Should not reach here

        # Test MRO behavior
        assert ConfigurationError.__mro__ == [
            ConfigurationError,
            ChattyCommanderError,
            ValueError,
            Exception,
            BaseException,
            object
        ]

    def test_exception_message_formatting(self):
        """Test exception message formatting with various inputs."""
        # Test with None message
        exc = ChattyCommanderError(None)
        assert str(exc) == "None"

        # Test with empty string
        exc = ChattyCommanderError("")
        assert str(exc) == ""

        # Test with special characters
        exc = ChattyCommanderError("Error with special chars: áéíóú ñ")
        assert "áéíóú" in str(exc)
        assert "ñ" in str(exc)

        # Test with very long message
        long_message = "A" * 1000
        exc = ChattyCommanderError(long_message)
        assert str(exc) == long_message
        assert len(str(exc)) == 1000

    def test_exception_custom_attributes(self):
        """Test adding custom attributes to exceptions."""
        exc = ChattyCommanderError("Base error")
        exc.error_code = 500
        exc.timestamp = "2024-01-01T00:00:00Z"
        exc.context = {"user_id": 123, "action": "test"}

        # Should be able to add custom attributes
        assert exc.error_code == 500
        assert exc.timestamp == "2024-01-01T00:00:00Z"
        assert exc.context == {"user_id": 123, "action": "test"}


class TestHelperFunctions:
    """Test helper utility functions."""

    def test_ensure_directory_exists(self):
        """Test ensure_directory_exists function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test creating new directory
            new_dir = os.path.join(temp_dir, "new_dir")
            assert not os.path.exists(new_dir)

            from chatty_commander.app.helpers import ensure_directory_exists
            ensure_directory_exists(new_dir)

            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)

            # Test with existing directory
            ensure_directory_exists(new_dir)  # Should not raise error

    def test_ensure_directory_exists_permissions(self):
        """Test ensure_directory_exists with permission issues."""
        from chatty_commander.app.helpers import ensure_directory_exists

        # Test with non-writable parent directory
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")

            with pytest.raises(PermissionError):
                ensure_directory_exists("/root/test_dir")

    def test_ensure_directory_exists_nested_paths(self):
        """Test ensure_directory_exists with nested paths."""
        from chatty_commander.app.helpers import ensure_directory_exists

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "level1", "level2", "level3")

            ensure_directory_exists(nested_path)

            assert os.path.exists(nested_path)
            assert os.path.isdir(nested_path)

    def test_format_command_output(self):
        """Test format_command_output function."""
        from chatty_commander.app.helpers import format_command_output

        # Test basic formatting
        output = "line1\nline2\nline3"
        formatted = format_command_output(output)
        assert formatted == "line1 | line2 | line3"

        # Test empty output
        formatted = format_command_output("")
        assert formatted == ""

        # Test whitespace only
        formatted = format_command_output("   \n  \t  \n  ")
        assert formatted == ""

        # Test single line
        formatted = format_command_output("single line")
        assert formatted == "single line"

        # Test mixed content
        output = "Error: command failed\nDetails: file not found\nSuggestion: check path"
        formatted = format_command_output(output)
        expected = "Error: command failed | Details: file not found | Suggestion: check path"
        assert formatted == expected

    def test_parse_model_keybindings(self):
        """Test parse_model_keybindings function."""
        from chatty_commander.app.helpers import parse_model_keybindings

        # Test normal case
        keybindings_str = "model1=ctrl+shift+1,model2=alt+F4,model3=ctrl+C"
        result = parse_model_keybindings(keybindings_str)

        expected = {
            "model1": "ctrl+shift+1",
            "model2": "alt+F4",
            "model3": "ctrl+C"
        }
        assert result == expected

        # Test empty string
        result = parse_model_keybindings("")
        assert result == {}

        # Test None input
        result = parse_model_keybindings(None)
        assert result == {}

        # Test single binding
        result = parse_model_keybindings("model1=ctrl+A")
        assert result == {"model1": "ctrl+A"}

        # Test with spaces around equals
        result = parse_model_keybindings("model1 = ctrl+A , model2 = alt+F4")
        expected = {
            "model1": "ctrl+A",
            "model2": "alt+F4"
        }
        assert result == expected

        # Test malformed input (no equals)
        result = parse_model_keybindings("model1 ctrl+A")
        assert result == {}

        # Test malformed input (empty key)
        result = parse_model_keybindings("=ctrl+A")
        assert result == {}

        # Test malformed input (empty value)
        result = parse_model_keybindings("model1=")
        assert result == {"model1": ""}

        # Test with special characters in model names
        result = parse_model_keybindings("model-1=ctrl+1,model_2=alt+2")
        expected = {
            "model-1": "ctrl+1",
            "model_2": "alt+2"
        }
        assert result == expected

    def test_parse_model_keybindings_edge_cases(self):
        """Test parse_model_keybindings edge cases."""
        from chatty_commander.app.helpers import parse_model_keybindings

        # Test with extra whitespace
        result = parse_model_keybindings("  model1 = ctrl+1  ,  model2 = alt+2  ")
        expected = {
            "model1": "ctrl+1",
            "model2": "alt+2"
        }
        assert result == expected

        # Test with empty pairs
        result = parse_model_keybindings("model1=ctrl+1,,model2=alt+2")
        expected = {
            "model1": "ctrl+1",
            "model2": "alt+2"
        }
        assert result == expected

        # Test with multiple separators
        result = parse_model_keybindings("model1=ctrl+1,model2=alt+2,model3=ctrl+3")
        expected = {
            "model1": "ctrl+1",
            "model2": "alt+2",
            "model3": "ctrl+3"
        }
        assert result == expected

        # Test with very long model names and keybindings
        long_model = "a" * 100
        long_binding = "ctrl+" * 20 + "A"
        result = parse_model_keybindings(f"{long_model}={long_binding}")
        assert result == {long_model: long_binding}

    def test_helper_function_error_handling(self):
        """Test error handling in helper functions."""
        from chatty_commander.app.helpers import (
            ensure_directory_exists,
            format_command_output,
        )

        # Test ensure_directory_exists with invalid path
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs', side_effect=OSError("Disk full")):
                with pytest.raises(OSError):
                    ensure_directory_exists("/invalid/path")

        # Test format_command_output with None
        result = format_command_output(None)
        assert result == ""

        # Test parse_model_keybindings with various invalid inputs
        from chatty_commander.app.helpers import parse_model_keybindings

        # Invalid format should be handled gracefully
        result = parse_model_keybindings("invalid=format,another=bad=format")
        assert result == {}

    def test_helper_function_integration(self):
        """Test helper functions working together."""
        from chatty_commander.app.helpers import (
            ensure_directory_exists,
            format_command_output,
            parse_model_keybindings,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory
            test_dir = os.path.join(temp_dir, "config")
            ensure_directory_exists(test_dir)

            # Format some command output
            command_result = "Configuration loaded successfully\nModel initialized\nReady for commands"
            formatted = format_command_output(command_result)
            assert " | " in formatted

            # Parse keybindings
            keybindings = parse_model_keybindings("config=ctrl+shift+C,load=ctrl+L,save=ctrl+S")
            assert len(keybindings) == 3
            assert keybindings["config"] == "ctrl+shift+C"

    def test_helper_function_with_mock_os(self):
        """Test helper functions with mocked os module."""
        from chatty_commander.app.helpers import ensure_directory_exists

        with patch('os.path.exists') as mock_exists:
            with patch('os.makedirs') as mock_makedirs:
                mock_exists.return_value = False

                ensure_directory_exists("/test/path")

                mock_exists.assert_called_once_with("/test/path")
                mock_makedirs.assert_called_once_with("/test/path")

    def test_format_command_output_performance(self):
        """Test format_command_output performance with large inputs."""
        from chatty_commander.app.helpers import format_command_output

        # Test with large output
        large_output = "\n".join([f"line_{i}" for i in range(1000)])
        result = format_command_output(large_output)

        assert len(result) > 0
        assert " | " in result
        assert result.count(" | ") == 999  # 1000 lines should have 999 separators

    def test_parse_model_keybindings_performance(self):
        """Test parse_model_keybindings performance with many bindings."""
        from chatty_commander.app.helpers import parse_model_keybindings

        # Test with many keybindings
        bindings_list = [f"model_{i}=ctrl+{i}" for i in range(100)]
        bindings_str = ",".join(bindings_list)

        result = parse_model_keybindings(bindings_str)

        assert len(result) == 100
        assert result["model_50"] == "ctrl+50"
        assert result["model_99"] == "ctrl+99"

    def test_helper_functions_return_types(self):
        """Test return types of helper functions."""
        from chatty_commander.app.helpers import (
            ensure_directory_exists,
            format_command_output,
            parse_model_keybindings,
        )

        # ensure_directory_exists returns None
        result = ensure_directory_exists("/tmp")
        assert result is None

        # format_command_output returns string
        result = format_command_output("test")
        assert isinstance(result, str)

        # parse_model_keybindings returns dict
        result = parse_model_keybindings("test=ctrl+T")
        assert isinstance(result, dict)

    def test_helper_functions_idempotency(self):
        """Test that helper functions are idempotent."""
        from chatty_commander.app.helpers import (
            ensure_directory_exists,
            format_command_output,
            parse_model_keybindings,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test")

            # ensure_directory_exists should be idempotent
            ensure_directory_exists(test_dir)
            ensure_directory_exists(test_dir)  # Second call should not fail

            # format_command_output should be deterministic
            test_output = "line1\nline2"
            result1 = format_command_output(test_output)
            result2 = format_command_output(test_output)
            assert result1 == result2

            # parse_model_keybindings should be deterministic
            test_bindings = "model1=ctrl+1,model2=ctrl+2"
            result1 = parse_model_keybindings(test_bindings)
            result2 = parse_model_keybindings(test_bindings)
            assert result1 == result2
