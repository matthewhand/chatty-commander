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
URL command execution tests for CommandExecutor.
"""

from unittest.mock import Mock

import pytest


class TestCommandExecutorURL:
    """Test URL command execution functionality."""

    def test_simple_url(self, command_executor, mock_dependencies):
        """Test execution of simple URL."""
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("test_url")
        assert result is True
        mock_requests.get.assert_called_once_with("http://example.com")

    def test_https_url(self, command_executor, mock_config, mock_dependencies):
        """Test execution of HTTPS URL."""
        mock_config.model_actions = {
            "https_url": {"action": "url", "url": "https://secure.example.com"}
        }
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("https_url")
        assert result is True
        mock_requests.get.assert_called_once_with("https://secure.example.com")

    def test_url_with_path(self, command_executor, mock_config, mock_dependencies):
        """Test URL with path."""
        mock_config.model_actions = {
            "path_url": {"action": "url", "url": "http://example.com/path/to/resource"}
        }
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("path_url")
        assert result is True
        mock_requests.get.assert_called_once_with("http://example.com/path/to/resource")

    def test_url_with_query_params(
        self, command_executor, mock_config, mock_dependencies
    ):
        """Test URL with query parameters."""
        mock_config.model_actions = {
            "query_url": {
                "action": "url",
                "url": "http://example.com?param1=value1&param2=value2",
            }
        }
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("query_url")
        assert result is True
        mock_requests.get.assert_called_once_with(
            "http://example.com?param1=value1&param2=value2"
        )

    def test_url_with_fragment(self, command_executor, mock_config, mock_dependencies):
        """Test URL with fragment."""
        mock_config.model_actions = {
            "fragment_url": {"action": "url", "url": "http://example.com#section1"}
        }
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("fragment_url")
        assert result is True
        mock_requests.get.assert_called_once_with("http://example.com#section1")

    def test_url_failure(self, command_executor, mock_dependencies):
        """Test handling of URL request failure."""
        mock_pg, mock_requests = mock_dependencies
        mock_requests.get.side_effect = Exception("Failed to fetch URL")

        result = command_executor.execute_command("test_url")
        assert result is False

    def test_empty_url(self, command_executor, mock_config, mock_dependencies):
        """Test empty URL."""
        mock_config.model_actions = {"empty_url": {"action": "url", "url": ""}}
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("empty_url")
        assert result is True
        mock_requests.get.assert_called_once_with("")

    def test_none_url(self, command_executor, mock_config, mock_dependencies):
        """Test None URL."""
        mock_config.model_actions = {"none_url": {"action": "url", "url": None}}

        result = command_executor.execute_command("none_url")
        assert result is False

    def test_invalid_url_format(self, command_executor, mock_config, mock_dependencies):
        """Test invalid URL format."""
        mock_config.model_actions = {
            "invalid_url": {"action": "url", "url": "not-a-valid-url"}
        }
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("invalid_url")
        assert result is True
        mock_requests.get.assert_called_once_with("not-a-valid-url")

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
    def test_various_url_schemes(
        self, command_executor, mock_config, mock_dependencies, url
    ):
        """Test various URL schemes."""
        mock_config.model_actions = {"scheme_url": {"action": "url", "url": url}}
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("scheme_url")
        assert result is True
        mock_requests.get.assert_called_once_with(url)

    def test_url_with_special_characters(
        self, command_executor, mock_config, mock_dependencies
    ):
        """Test URL with special characters."""
        url = "http://example.com/path with spaces/file-name_123.html?param=value&other=val+ue"
        mock_config.model_actions = {"special_url": {"action": "url", "url": url}}
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("special_url")
        assert result is True
        mock_requests.get.assert_called_once_with(url)

    def test_url_with_unicode(self, command_executor, mock_config, mock_dependencies):
        """Test URL with Unicode characters."""
        url = "http://example.com/测试/路径?参数=值"
        mock_config.model_actions = {"unicode_url": {"action": "url", "url": url}}
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("unicode_url")
        assert result is True
        mock_requests.get.assert_called_once_with(url)
