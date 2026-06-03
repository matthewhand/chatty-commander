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
Tests for generate_api_docs facade module.

Tests CLI delegation and main entry point.
"""

from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.tools.generate_api_docs import main


class TestMainFunction:
    """Tests for main function."""

    def test_delegates_to_cli_main(self):
        """Test that main delegates to cli.main."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = 0
            
            result = main()
            
            mock_main.assert_called_once_with(None)
            assert result == 0

    def test_returns_exit_code_from_cli(self):
        """Test that main returns exit code from CLI."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = 1
            
            result = main()
            
            assert result == 1

    def test_cli_error_handling(self):
        """Test that CLI errors are propagated."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.side_effect = Exception("CLI error")
            
            with pytest.raises(Exception) as exc_info:
                main()
            
            assert "CLI error" in str(exc_info.value)

    def test_main_returns_int(self):
        """Test that main returns an integer exit code."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = 0
            
            result = main()
            
            assert isinstance(result, int)


class TestMainIntegration:
    """Integration-style tests."""

    def test_main_with_successful_cli(self):
        """Test main when CLI succeeds."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = 0
            
            result = main()
            
            assert result == 0

    def test_main_with_failed_cli(self):
        """Test main when CLI fails."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = 1
            
            result = main()
            
            assert result == 1


class TestEdgeCases:
    """Edge case tests."""

    def test_main_with_none_return(self):
        """Test main when CLI returns None."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            mock_main.return_value = None
            
            result = main()
            
            assert result is None

    def test_main_passes_none_argument(self):
        """Test that main passes None to cli.main."""
        with patch("src.chatty_commander.tools.generate_api_docs._main") as mock_main:
            main()
            
            args = mock_main.call_args[0]
            assert args[0] is None
