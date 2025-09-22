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

import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from chatty_commander.utils.logger import (
    HTTPLogHandler,
    JSONFormatter,
    report_error,
    setup_logger,
)


class TestLogger(unittest.TestCase):
    @patch("chatty_commander.utils.logger.os.makedirs")
    @patch("chatty_commander.utils.logger.RotatingFileHandler")
    def test_setup_logger(self, mock_handler, mock_makedirs):
        mock_logger = MagicMock()
        with patch(
            "chatty_commander.utils.logger.logging.getLogger"
        ) as mock_get_logger:
            mock_get_logger.return_value = mock_logger
            logger = setup_logger("test_logger", "test.log", level=logging.DEBUG)
            mock_makedirs.assert_called_once_with(os.path.dirname("test.log"))
            mock_handler.assert_called_once_with(
                "test.log", maxBytes=1000000, backupCount=5
            )
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
            mock_logger.addHandler.assert_called_once()
            self.assertEqual(logger, mock_logger)

    @patch("chatty_commander.utils.logger.RotatingFileHandler")
    @patch("chatty_commander.utils.logger.logging.getLogger")
    def test_setup_logger_directory_exists(self, mock_get_logger, mock_handler):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        with patch("chatty_commander.utils.logger.os.path.exists", return_value=True):
            with patch("chatty_commander.utils.logger.os.makedirs") as mock_makedirs:
                logger = setup_logger("test", "existing/dir/log.log")
                mock_makedirs.assert_not_called()
                mock_handler.assert_called_once_with(
                    "existing/dir/log.log", maxBytes=1000000, backupCount=5
                )
                mock_logger.addHandler.assert_called_once()
                self.assertEqual(logger, mock_logger)

    def test_setup_logger_no_file(self):
        """Test setup_logger without log file"""
        mock_logger = MagicMock()
        with patch(
            "chatty_commander.utils.logger.logging.getLogger"
        ) as mock_get_logger:
            mock_get_logger.return_value = mock_logger
            _ = setup_logger("test_logger")
            mock_logger.setLevel.assert_called_once_with(logging.INFO)
            # Should only add console handler, not file handler
            self.assertEqual(mock_logger.addHandler.call_count, 1)

    def test_setup_logger_makedirs_error(self):
        """Test setup_logger when makedirs fails"""
        mock_logger = MagicMock()
        with patch(
            "chatty_commander.utils.logger.logging.getLogger"
        ) as mock_get_logger:
            mock_get_logger.return_value = mock_logger
            with patch(
                "chatty_commander.utils.logger.os.makedirs",
                side_effect=OSError("Permission denied"),
            ):
                with patch("chatty_commander.utils.logger.RotatingFileHandler") as _:
                    _ = setup_logger("test_logger", "test.log")
                    # Should still work, just without file handler
                    mock_logger.addHandler.assert_called_once()


class TestJSONFormatter(unittest.TestCase):
    def test_json_formatter_basic(self):
        """Test JSONFormatter basic functionality"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["name"], "test_logger")
        self.assertEqual(data["message"], "Test message")
        self.assertIn("time", data)

    def test_json_formatter_with_exception(self):
        """Test JSONFormatter with exception info"""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            result = formatter.format(record)
            data = json.loads(result)

            self.assertEqual(data["level"], "ERROR")
            self.assertEqual(data["message"], "Error occurred")
            self.assertIn("exception", data)
            self.assertIn("ValueError: Test exception", data["exception"])


class TestHTTPLogHandler(unittest.TestCase):
    def test_http_log_handler_init(self):
        """Test HTTPLogHandler initialization"""
        handler = HTTPLogHandler("http://example.com/logs", timeout=10)
        self.assertEqual(handler.url, "http://example.com/logs")
        self.assertEqual(handler.timeout, 10)

    def test_http_log_handler_emit_no_requests(self):
        """Test HTTPLogHandler emit when requests is not available"""
        handler = HTTPLogHandler("http://example.com/logs")
        handler._requests = None

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise an exception
        handler.emit(record)

    @patch("requests.post")
    def test_http_log_handler_emit_success(self, mock_post):
        """Test HTTPLogHandler emit success"""
        handler = HTTPLogHandler("http://example.com/logs")

        # Mock requests module
        mock_requests = MagicMock()
        mock_requests.post = mock_post
        handler._requests = mock_requests

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://example.com/logs")
        self.assertEqual(kwargs["timeout"], 5)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    @patch("requests.post")
    def test_http_log_handler_emit_exception(self, mock_post):
        """Test HTTPLogHandler emit handles exceptions gracefully"""
        handler = HTTPLogHandler("http://example.com/logs")

        # Mock requests module
        mock_requests = MagicMock()
        mock_requests.post = mock_post
        mock_post.side_effect = Exception("Network error")
        handler._requests = mock_requests

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise an exception
        handler.emit(record)


class TestReportError(unittest.TestCase):
    def test_report_error_basic(self):
        """Test report_error basic functionality"""
        error = ValueError("Test error")
        # Just test that it doesn't raise an exception
        report_error(error)

    def test_report_error_with_context(self):
        """Test report_error with context"""
        error = ValueError("Test error")
        context = {"operation": "test_operation", "user": "test_user"}
        # Just test that it doesn't raise an exception
        report_error(error, context=context)


if __name__ == "__main__":
    unittest.main()
