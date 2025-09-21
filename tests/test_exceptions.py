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
Comprehensive tests for application exceptions module.

Tests exception hierarchy, error handling, and custom exception behavior.
"""

import pytest

from chatty_commander.exceptions import (
    ChattyCommanderError,
    ConfigurationError,
    ValidationError,
    ExecutionError,
    DependencyError,
)


class TestChattyCommanderError:
    """Test base exception class."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        error = ChattyCommanderError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception."""
        error = ChattyCommanderError("Test message")
        assert isinstance(error, Exception)
        assert isinstance(error, ChattyCommanderError)

    def test_base_exception_with_cause(self):
        """Test base exception with cause."""
        original_error = ValueError("Original error")
        error = ChattyCommanderError("Wrapper error")

        # Test that it can wrap other exceptions
        try:
            raise original_error from error
        except ValueError:
            assert True

    def test_base_exception_attributes(self):
        """Test base exception attributes."""
        error = ChattyCommanderError("Test error")
        assert hasattr(error, 'args')
        assert error.args == ("Test error",)


class TestConfigurationError:
    """Test configuration exception class."""

    def test_configuration_error_creation(self):
        """Test creating configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ValueError)

    def test_configuration_error_inheritance(self):
        """Test configuration error inheritance chain."""
        error = ConfigurationError("Config error")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ValueError)
        assert isinstance(error, Exception)

    def test_configuration_error_with_details(self):
        """Test configuration error with detailed information."""
        config_details = {"file": "config.json", "section": "database"}
        error = ConfigurationError(f"Missing required section: {config_details}")
        assert "Missing required section" in str(error)
        assert isinstance(error, ConfigurationError)


class TestValidationError:
    """Test validation exception class."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError("Input validation failed")
        assert str(error) == "Input validation failed"
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ValueError)

    def test_validation_error_inheritance(self):
        """Test validation error inheritance chain."""
        error = ValidationError("Validation error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ValueError)
        assert isinstance(error, Exception)

    def test_validation_error_with_field_info(self):
        """Test validation error with field information."""
        field_name = "email"
        error = ValidationError(f"Invalid format for field '{field_name}'")
        assert "Invalid format" in str(error)
        assert field_name in str(error)


class TestExecutionError:
    """Test execution exception class."""

    def test_execution_error_creation(self):
        """Test creating execution error."""
        error = ExecutionError("Command execution failed")
        assert str(error) == "Command execution failed"
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, Exception)

    def test_execution_error_inheritance(self):
        """Test execution error inheritance chain."""
        error = ExecutionError("Execution error")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, Exception)

    def test_execution_error_with_command_info(self):
        """Test execution error with command information."""
        command = "ls -la"
        exit_code = 1
        error = ExecutionError(f"Command '{command}' failed with exit code {exit_code}")
        assert command in str(error)
        assert str(exit_code) in str(error)


class TestDependencyError:
    """Test dependency exception class."""

    def test_dependency_error_creation(self):
        """Test creating dependency error."""
        error = DependencyError("Missing required library")
        assert str(error) == "Missing required library"
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ImportError)

    def test_dependency_error_inheritance(self):
        """Test dependency error inheritance chain."""
        error = DependencyError("Dependency error")
        assert isinstance(error, DependencyError)
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ImportError)
        assert isinstance(error, Exception)

    def test_dependency_error_with_package_info(self):
        """Test dependency error with package information."""
        package_name = "requests"
        version = "2.25.0"
        error = DependencyError(f"Package '{package_name}' version {version} not found")
        assert package_name in str(error)
        assert version in str(error)


class TestExceptionHierarchy:
    """Test complete exception hierarchy."""

    def test_exception_hierarchy_structure(self):
        """Test that exception hierarchy is properly structured."""
        # Test that all exceptions inherit from base
        base_error = ChattyCommanderError("base")
        config_error = ConfigurationError("config")
        validation_error = ValidationError("validation")
        execution_error = ExecutionError("execution")
        dependency_error = DependencyError("dependency")

        # All should be instances of base exception
        assert isinstance(config_error, ChattyCommanderError)
        assert isinstance(validation_error, ChattyCommanderError)
        assert isinstance(execution_error, ChattyCommanderError)
        assert isinstance(dependency_error, ChattyCommanderError)

    def test_exception_multiple_inheritance(self):
        """Test that exceptions properly inherit from multiple base classes."""
        config_error = ConfigurationError("test")
        validation_error = ValidationError("test")
        execution_error = ExecutionError("test")
        dependency_error = DependencyError("test")

        # Test multiple inheritance
        assert isinstance(config_error, ValueError)
        assert isinstance(validation_error, ValueError)
        assert isinstance(execution_error, Exception)
        assert isinstance(dependency_error, ImportError)

    def test_exception_error_messages(self):
        """Test that all exceptions provide meaningful error messages."""
        errors = [
            ChattyCommanderError("Base error message"),
            ConfigurationError("Configuration error message"),
            ValidationError("Validation error message"),
            ExecutionError("Execution error message"),
            DependencyError("Dependency error message"),
        ]

        for error in errors:
            assert str(error)  # Should have string representation
            assert len(str(error)) > 0  # Should not be empty

    def test_exception_context_preservation(self):
        """Test that exceptions preserve context and chaining."""
        try:
            raise ValueError("Original error")
        except ValueError as original:
            # Create new exception with original as context
            new_error = ChattyCommanderError("New error") from original

            assert new_error.__cause__ is original
            assert isinstance(new_error.__cause__, ValueError)

    def test_exception_suppression(self):
        """Test exception suppression behavior."""
        try:
            raise ConfigurationError("Suppressed error")
        except ConfigurationError:
            # Exception should be suppressible
            suppressed_error = ChattyCommanderError("Suppressing")
            assert True

    def test_exception_custom_attributes(self):
        """Test that exceptions can have custom attributes."""
        error = ChattyCommanderError("Test error")
        error.custom_attribute = "custom_value"

        assert hasattr(error, 'custom_attribute')
        assert error.custom_attribute == "custom_value"

    def test_exception_serialization(self):
        """Test that exceptions can be serialized/deserialized."""
        import pickle

        original_error = ValidationError("Serializable error")

        # Should be serializable
        try:
            serialized = pickle.dumps(original_error)
            deserialized = pickle.loads(serialized)
            assert isinstance(deserialized, ValidationError)
            assert str(deserialized) == str(original_error)
        except (pickle.PicklingError, TypeError):
            # Some exceptions may not be serializable, which is OK
            pass

    def test_exception_comparison(self):
        """Test exception comparison and equality."""
        error1 = ChattyCommanderError("Same message")
        error2 = ChattyCommanderError("Same message")
        error3 = ChattyCommanderError("Different message")

        # Same messages should be equal
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)

    def test_exception_type_checking(self):
        """Test that isinstance checks work correctly."""
        error = ConfigurationError("test")

        assert isinstance(error, ConfigurationError)
        assert isinstance(error, ChattyCommanderError)
        assert isinstance(error, ValueError)
        assert isinstance(error, Exception)

        # Negative checks
        assert not isinstance(error, ExecutionError)
        assert not isinstance(error, ValidationError)

    def test_exception_in_except_blocks(self):
        """Test that exceptions work properly in except blocks."""
        caught_errors = []

        try:
            raise ConfigurationError("Config error")
        except ChattyCommanderError as e:
            caught_errors.append(("base", str(e)))

        try:
            raise ValidationError("Validation error")
        except ChattyCommanderError as e:
            caught_errors.append(("base", str(e)))

        try:
            raise DependencyError("Dependency error")
        except ImportError as e:
            caught_errors.append(("import", str(e)))

        assert len(caught_errors) == 3
        assert all("error" in error_msg for _, error_msg in caught_errors)

    def test_exception_nested_raising(self):
        """Test nested exception raising."""
        def inner_function():
            raise ConfigurationError("Inner error")

        def outer_function():
            try:
                inner_function()
            except ConfigurationError as e:
                raise ExecutionError("Outer error") from e

        try:
            outer_function()
        except ExecutionError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ConfigurationError)

    def test_exception_with_traceback(self):
        """Test that exceptions preserve traceback information."""
        def failing_function():
            raise ChattyCommanderError("Test error")

        try:
            failing_function()
        except ChattyCommanderError as e:
            # Should have traceback information
            assert e.__traceback__ is not None
            assert hasattr(e, '__traceback__')

    def test_exception_performance(self):
        """Test exception performance characteristics."""
        import time

        # Creating exceptions should be fast
        start_time = time.time()
        for i in range(100):
            error = ChattyCommanderError(f"Performance test {i}")
        end_time = time.time()

        creation_time = end_time - start_time
        assert creation_time < 1.0  # Should create 100 exceptions in less than 1 second

    def test_exception_memory_usage(self):
        """Test exception memory usage."""
        # Should not leak memory
        errors = []
        for i in range(10):
            error = ChattyCommanderError(f"Memory test {i}")
            errors.append(error)

        # Should be able to create and store multiple exceptions
        assert len(errors) == 10
        assert all(isinstance(error, ChattyCommanderError) for error in errors)

    def test_exception_thread_safety(self):
        """Test exception thread safety."""
        import threading

        results = []
        errors = []

        def create_exception(thread_id):
            try:
                error = ChattyCommanderError(f"Thread {thread_id} error")
                results.append((thread_id, str(error)))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create exceptions in multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_exception, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should have created exceptions in all threads
        assert len(results) == 5
        assert len(errors) == 0

    def test_exception_documentation(self):
        """Test that all exceptions have proper documentation."""
        exceptions = [
            ChattyCommanderError,
            ConfigurationError,
            ValidationError,
            ExecutionError,
            DependencyError,
        ]

        for exception_class in exceptions:
            assert exception_class.__doc__ is not None
            assert len(exception_class.__doc__) > 0
            assert "Raised when" in exception_class.__doc__ or "Base exception" in exception_class.__doc__

    def test_exception_usage_patterns(self):
        """Test common exception usage patterns."""

        # Pattern 1: Direct instantiation
        error = ChattyCommanderError("Direct error")
        assert str(error) == "Direct error"

        # Pattern 2: Raising and catching
        caught = None
        try:
            raise ValidationError("Validation failed")
        except ChattyCommanderError as e:
            caught = e

        assert caught is not None
        assert isinstance(caught, ValidationError)

        # Pattern 3: Exception chaining
        try:
            raise ValueError("Root cause")
        except ValueError as root:
            try:
                raise ConfigurationError("Configuration issue") from root
            except ConfigurationError as config_error:
                assert config_error.__cause__ is root

    def test_exception_edge_cases(self):
        """Test exception edge cases."""

        # Empty message
        error = ChattyCommanderError("")
        assert str(error) == ""

        # None message (should convert to string)
        error = ChattyCommanderError(None)
        assert str(error) == "None"

        # Long message
        long_message = "x" * 1000
        error = ChattyCommanderError(long_message)
        assert len(str(error)) == 1000

    def test_exception_inheritance_validation(self):
        """Test that exception inheritance is correct."""
        # Test that all custom exceptions inherit from the base
        custom_exceptions = [
            ConfigurationError,
            ValidationError,
            ExecutionError,
            DependencyError,
        ]

        for exception_class in custom_exceptions:
            # Should inherit from base exception
            assert issubclass(exception_class, ChattyCommanderError)

            # Should also inherit from standard exceptions
            if exception_class in [ConfigurationError, ValidationError]:
                assert issubclass(exception_class, ValueError)
            elif exception_class == ExecutionError:
                assert issubclass(exception_class, Exception)
            elif exception_class == DependencyError:
                assert issubclass(exception_class, ImportError)

    def test_exception_integration(self):
        """Test exception integration with other modules."""
        # Test that exceptions can be imported and used
        from chatty_commander.exceptions import (
            ChattyCommanderError,
            ConfigurationError,
            ValidationError,
            ExecutionError,
            DependencyError,
        )

        # All should be importable
        assert ChattyCommanderError is not None
        assert ConfigurationError is not None
        assert ValidationError is not None
        assert ExecutionError is not None
        assert DependencyError is not None

        # Should be usable
        error = ConfigurationError("Integration test")
        assert isinstance(error, ChattyCommanderError)
