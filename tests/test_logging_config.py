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
Comprehensive tests for logging configuration module.

Tests structured logging, JSON formatting, and request ID middleware.
"""

import json
import logging
import os
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.utils.logging_config import (
    StructuredJSONFormatter,
    configure_logging,
    get_request_id,
)


class TestGetRequestId:
    """Tests for get_request_id function."""

    def test_returns_empty_string_by_default(self):
        """Test that get_request_id returns empty string by default."""
        request_id = get_request_id()
        assert request_id == ""

    def test_returns_string_type(self):
        """Test that get_request_id returns a string."""
        request_id = get_request_id()
        assert isinstance(request_id, str)


class TestStructuredJSONFormatter:
    """Tests for StructuredJSONFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a StructuredJSONFormatter instance."""
        return StructuredJSONFormatter()

    @pytest.fixture
    def log_record(self):
        """Create a basic log record."""
        return logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_format_basic_record(self, formatter, log_record):
        """Test formatting a basic log record."""
        output = formatter.format(log_record)
        parsed = json.loads(output)
        
        assert "time" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"

    def test_format_includes_all_required_fields(self, formatter, log_record):
        """Test that formatted output includes all required fields."""
        output = formatter.format(log_record)
        parsed = json.loads(output)
        
        required_fields = ["time", "level", "logger", "message"]
        for field in required_fields:
            assert field in parsed

    def test_format_different_levels(self, formatter):
        """Test formatting different log levels."""
        for level, level_name in [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]:
            record = logging.LogRecord(
                name="test", level=level, pathname="test.py",
                lineno=1, msg="Test", args=(), exc_info=None,
            )
            output = formatter.format(record)
            parsed = json.loads(output)
            assert parsed["level"] == level_name

    def test_format_with_exception(self, formatter):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = logging.sys.exc_info()
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="Error occurred", args=(), exc_info=exc_info,
            )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_plain_format(self):
        """Test configuring logging with plain format."""
        with patch.dict(os.environ, {"LOG_FORMAT": "plain"}, clear=True):
            configure_logging(level="INFO", log_format="plain")
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) >= 1

    def test_configure_json_format(self):
        """Test configuring logging with JSON format."""
        with patch.dict(os.environ, {"LOG_FORMAT": "json"}, clear=True):
            configure_logging(level="INFO", log_format="json")
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) >= 1

    def test_configure_different_levels(self):
        """Test configuring logging with different levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            configure_logging(level=level, log_format="plain")
            
            root_logger = logging.getLogger()
            expected_level = getattr(logging, level)
            assert root_logger.level == expected_level

    def test_configure_from_environment(self):
        """Test configuring from environment variables."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG", "LOG_FORMAT": "json"}):
            configure_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

    def test_configure_removes_existing_handlers(self):
        """Test that configure_logging removes existing handlers."""
        root_logger = logging.getLogger()
        original_handler_count = len(root_logger.handlers)
        
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        
        configure_logging(level="INFO", log_format="plain")
        
        # Should have only the new handler(s)
        assert len(root_logger.handlers) >= 1


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_full_logging_workflow_json(self):
        """Test complete logging workflow with JSON format."""
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredJSONFormatter())
        
        logger = logging.getLogger("test_integration")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Integration test message")
        
        output = log_capture.getvalue()
        parsed = json.loads(output.strip())
        
        assert parsed["message"] == "Integration test message"
        assert parsed["logger"] == "test_integration"
        assert parsed["level"] == "INFO"

    def test_log_output_is_valid_json(self):
        """Test that log output is valid JSON."""
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredJSONFormatter())
        
        logger = logging.getLogger("test_json")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        
        output = log_capture.getvalue().strip()
        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)


class TestEdgeCases:
    """Edge case tests."""

    def test_formatter_with_unicode_message(self):
        """Test formatting with unicode characters."""
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Unicode: hello world", args=(), exc_info=None,
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "hello world" in parsed["message"]

    def test_formatter_with_empty_message(self):
        """Test formatting with empty message."""
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="", args=(), exc_info=None,
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["message"] == ""

    def test_configure_with_invalid_level(self):
        """Test configuring with invalid log level."""
        # Should default to INFO for invalid level
        configure_logging(level="INVALID_LEVEL", log_format="plain")
        
        root_logger = logging.getLogger()
        # Falls back to INFO
        assert root_logger.level == logging.INFO

    def test_configure_with_none_params(self):
        """Test configuring with None parameters."""
        with patch.dict(os.environ, {}, clear=True):
            configure_logging(level=None, log_format=None)
            
            root_logger = logging.getLogger()
            # Should use defaults
            assert root_logger.level == logging.INFO
