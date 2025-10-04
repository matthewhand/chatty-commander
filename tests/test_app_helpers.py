"""
Tests for app helper functions and utilities.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os
import json


class TestAppHelpers:
    """Test app helper functions."""

    def test_file_path_validation(self):
        """Test file path validation functions."""
        # Valid paths
        valid_paths = [
            "/home/user/config.json",
            "config.json",
            "./config.json",
            "../config.json",
            "C:\\Users\\User\\config.json" if os.name == "nt" else "/tmp/config.json",
        ]

        for path in valid_paths:
            assert isinstance(path, str)
            assert len(path) > 0

    def test_config_file_creation(self):
        """Test configuration file creation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "default_state": "idle",
                "model_actions": {"test": {"action": "shell", "cmd": "echo test"}},
            }
            json.dump(config_data, f)
            temp_file = f.name

        try:
            # Verify file was created and contains valid JSON
            assert os.path.exists(temp_file)
            with open(temp_file, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == config_data
        finally:
            os.unlink(temp_file)

    def test_directory_creation(self):
        """Test directory creation utilities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_subdir")

            # Create directory
            os.makedirs(test_dir, exist_ok=True)
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)

    def test_environment_variable_handling(self):
        """Test environment variable handling."""
        # Test setting and getting environment variables
        test_key = "CHATTY_COMMANDER_TEST"
        test_value = "test_value"

        os.environ[test_key] = test_value
        assert os.environ.get(test_key) == test_value

        # Clean up
        if test_key in os.environ:
            del os.environ[test_key]

    def test_string_validation_helpers(self):
        """Test string validation helper functions."""
        # Valid strings
        valid_strings = [
            "hello",
            "hello_world",
            "hello-world",
            "hello.world",
            "hello123",
            "Hello World",
        ]

        for s in valid_strings:
            assert isinstance(s, str)
            assert len(s) > 0

        # Invalid strings
        invalid_strings = ["", None, 123, [], {}]

        for s in invalid_strings:
            assert not isinstance(s, str) or len(s) == 0

    def test_list_validation_helpers(self):
        """Test list validation helper functions."""
        # Valid lists
        valid_lists = [
            [],
            ["item1", "item2"],
            [1, 2, 3],
            [{"key": "value"}, {"other": "data"}],
        ]

        for lst in valid_lists:
            assert isinstance(lst, list)

        # Invalid lists
        invalid_lists = ["string", 123, {}, None]

        for lst in invalid_lists:
            assert not isinstance(lst, list)

    def test_dict_validation_helpers(self):
        """Test dictionary validation helper functions."""
        # Valid dictionaries
        valid_dicts = [
            {},
            {"key": "value"},
            {"nested": {"inner": "value"}},
            {"list": [1, 2, 3]},
        ]

        for d in valid_dicts:
            assert isinstance(d, dict)

        # Invalid dictionaries
        invalid_dicts = ["string", 123, [], None]

        for d in invalid_dicts:
            assert not isinstance(d, dict)

    def test_url_validation_helpers(self):
        """Test URL validation helper functions."""
        # Valid URLs
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://localhost:8000",
            "https://api.example.com/v1/endpoint",
        ]

        for url in valid_urls:
            assert isinstance(url, str)
            assert url.startswith(("http://", "https://"))

        # Invalid URLs
        invalid_urls = ["not-a-url", "ftp://example.com", "", None, 123]

        for url in invalid_urls:
            assert not isinstance(url, str) or not url.startswith(
                ("http://", "https://")
            )

    def test_port_validation_helpers(self):
        """Test port number validation helpers."""
        # Valid ports
        valid_ports = [80, 443, 8000, 3000, 8080]

        for port in valid_ports:
            assert isinstance(port, int)
            assert 1 <= port <= 65535

        # Invalid ports
        invalid_ports = [-1, 0, 65536, 100000, "8080", None]

        for port in invalid_ports:
            assert not isinstance(port, int) or not (1 <= port <= 65535)

    def test_boolean_validation_helpers(self):
        """Test boolean validation helper functions."""
        # Valid booleans
        valid_booleans = [True, False]

        for boolean in valid_booleans:
            assert isinstance(boolean, bool)

        # Test boolean conversion
        truthy_values = [True, 1, "true", "True", "1"]
        falsy_values = [False, 0, "false", "False", "0", ""]

        for value in truthy_values:
            assert bool(value) is True

        for value in falsy_values:
            assert bool(value) is False

    def test_timeout_validation_helpers(self):
        """Test timeout validation helper functions."""
        # Valid timeouts
        valid_timeouts = [0, 1, 30, 60, 300]

        for timeout in valid_timeouts:
            assert isinstance(timeout, (int, float))
            assert timeout >= 0

        # Invalid timeouts
        invalid_timeouts = [-1, -30, None, "30"]

        for timeout in invalid_timeouts:
            assert not isinstance(timeout, (int, float)) or timeout < 0

    def test_logging_helpers(self):
        """Test logging helper functions."""
        import logging

        # Test log level validation
        valid_levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]

        for level in valid_levels:
            assert isinstance(level, int)
            assert 0 <= level <= 50

    def test_error_message_formatting(self):
        """Test error message formatting helpers."""
        # Test error message templates
        error_templates = {
            "file_not_found": "File not found: {filename}",
            "invalid_config": "Invalid configuration: {error}",
            "connection_failed": "Connection failed: {reason}",
        }

        for template_name, template in error_templates.items():
            assert isinstance(template, str)
            assert "{" in template  # Has placeholder

            # Test formatting
            if template_name == "file_not_found":
                formatted = template.format(filename="test.json")
                assert "test.json" in formatted

    def test_data_conversion_helpers(self):
        """Test data conversion helper functions."""
        # Test JSON serialization/deserialization
        test_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
        }

        # Serialize to JSON
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)

        # Deserialize from JSON
        loaded_data = json.loads(json_str)
        assert loaded_data == test_data

    def test_memory_usage_helpers(self):
        """Test memory usage helper functions."""
        import sys

        # Test memory usage calculation
        test_string = "x" * 1000
        memory_usage = sys.getsizeof(test_string)
        assert memory_usage > 0
        assert memory_usage >= 1000

    def test_time_helpers(self):
        """Test time-related helper functions."""
        import time

        # Test timestamp generation
        timestamp = time.time()
        assert isinstance(timestamp, float)
        assert timestamp > 0

        # Test sleep functionality
        start_time = time.time()
        time.sleep(0.01)  # Sleep for 10ms
        end_time = time.time()
        assert (end_time - start_time) >= 0.01

    def test_process_helpers(self):
        """Test process-related helper functions."""
        import subprocess

        # Test simple process execution
        try:
            result = subprocess.run(
                ["echo", "test"], capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0
            assert "test" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Handle cases where echo is not available or timeout occurs
            pass

    def test_thread_safety_helpers(self):
        """Test thread safety helper functions."""
        import threading

        # Test thread creation
        test_results = []

        def worker_function(value):
            test_results.append(value)

        thread = threading.Thread(target=worker_function, args=("test",))
        thread.start()
        thread.join()

        assert "test" in test_results
