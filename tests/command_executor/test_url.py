"""
URL command execution tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorURL:
    """Test URL command execution functionality."""

    @patch("webbrowser.open")
    def test_simple_url(self, mock_open, command_executor):
        """Test execution of simple URL."""
        result = command_executor.execute_command("test_url")
        assert result is True
        mock_open.assert_called_once_with("http://example.com")

    @patch("webbrowser.open")
    def test_https_url(self, mock_open, command_executor, mock_config):
        """Test execution of HTTPS URL."""
        mock_config.model_actions = {
            "https_url": {"action": "url", "url": "https://secure.example.com"}
        }

        result = command_executor.execute_command("https_url")
        assert result is True
        mock_open.assert_called_once_with("https://secure.example.com")

    @patch("webbrowser.open")
    def test_url_with_path(self, mock_open, command_executor, mock_config):
        """Test URL with path."""
        mock_config.model_actions = {
            "path_url": {"action": "url", "url": "http://example.com/path/to/resource"}
        }

        result = command_executor.execute_command("path_url")
        assert result is True
        mock_open.assert_called_once_with("http://example.com/path/to/resource")

    @patch("webbrowser.open")
    def test_url_with_query_params(self, mock_open, command_executor, mock_config):
        """Test URL with query parameters."""
        mock_config.model_actions = {
            "query_url": {
                "action": "url",
                "url": "http://example.com?param1=value1&param2=value2",
            }
        }

        result = command_executor.execute_command("query_url")
        assert result is True
        mock_open.assert_called_once_with(
            "http://example.com?param1=value1&param2=value2"
        )

    @patch("webbrowser.open")
    def test_url_with_fragment(self, mock_open, command_executor, mock_config):
        """Test URL with fragment."""
        mock_config.model_actions = {
            "fragment_url": {"action": "url", "url": "http://example.com#section1"}
        }

        result = command_executor.execute_command("fragment_url")
        assert result is True
        mock_open.assert_called_once_with("http://example.com#section1")

    @patch("webbrowser.open")
    def test_url_failure(self, mock_open, command_executor):
        """Test handling of URL opening failure."""
        mock_open.side_effect = Exception("Failed to open URL")

        result = command_executor.execute_command("test_url")
        assert result is False

    @patch("webbrowser.open")
    def test_empty_url(self, mock_open, command_executor, mock_config):
        """Test empty URL."""
        mock_config.model_actions = {"empty_url": {"action": "url", "url": ""}}

        result = command_executor.execute_command("empty_url")
        assert result is True
        mock_open.assert_called_once_with("")

    @patch("webbrowser.open")
    def test_none_url(self, mock_open, command_executor, mock_config):
        """Test None URL."""
        mock_config.model_actions = {"none_url": {"action": "url", "url": None}}

        result = command_executor.execute_command("none_url")
        assert result is False

    @patch("webbrowser.open")
    def test_invalid_url_format(self, mock_open, command_executor, mock_config):
        """Test invalid URL format."""
        mock_config.model_actions = {
            "invalid_url": {"action": "url", "url": "not-a-valid-url"}
        }

        result = command_executor.execute_command("invalid_url")
        assert result is True
        mock_open.assert_called_once_with("not-a-valid-url")

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "https://api.example.com/v1/users",
            "ftp://files.example.com/data",
            "file:///path/to/local/file",
            "mailto:user@example.com",
            "tel:+1234567890",
        ],
    )
    @patch("webbrowser.open")
    def test_various_url_schemes(self, mock_open, command_executor, mock_config, url):
        """Test various URL schemes."""
        mock_config.model_actions = {"scheme_url": {"action": "url", "url": url}}

        result = command_executor.execute_command("scheme_url")
        assert result is True
        mock_open.assert_called_once_with(url)

    @patch("webbrowser.open")
    def test_url_with_special_characters(
        self, mock_open, command_executor, mock_config
    ):
        """Test URL with special characters."""
        url = "http://example.com/path with spaces/file-name_123.html?param=value&other=val+ue"
        mock_config.model_actions = {"special_url": {"action": "url", "url": url}}

        result = command_executor.execute_command("special_url")
        assert result is True
        mock_open.assert_called_once_with(url)

    @patch("webbrowser.open")
    def test_url_with_unicode(self, mock_open, command_executor, mock_config):
        """Test URL with Unicode characters."""
        url = "http://example.com/测试/路径?参数=值"
        mock_config.model_actions = {"unicode_url": {"action": "url", "url": url}}

        result = command_executor.execute_command("unicode_url")
        assert result is True
        mock_open.assert_called_once_with(url)
