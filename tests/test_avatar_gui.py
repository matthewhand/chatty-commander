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
Tests for avatar GUI launcher module.

Tests pywebview-based transparent avatar window.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.avatars.avatar_gui import _avatar_index_path, run_avatar_gui


class TestAvatarIndexPath:
    """Tests for _avatar_index_path function."""

    def test_returns_path_object(self):
        """Test that function returns a Path object."""
        result = _avatar_index_path()
        assert isinstance(result, Path)

    def test_path_ends_with_index_html(self):
        """Test that path ends with index.html."""
        result = _avatar_index_path()
        assert result.name == "index.html"

    def test_path_contains_webui_avatar(self):
        """Test that path contains webui/avatar directories."""
        result = _avatar_index_path()
        path_str = str(result)
        assert "webui" in path_str
        assert "avatar" in path_str


class TestRunAvatarGui:
    """Tests for run_avatar_gui function."""

    def test_returns_2_when_webview_missing(self):
        """Test returns error code when pywebview not installed."""
        with patch("src.chatty_commander.avatars.avatar_gui.webview", None):
            result = run_avatar_gui()
            assert result == 2

    def test_returns_2_when_index_html_missing(self):
        """Test returns error when avatar index.html not found."""
        mock_webview = Mock()
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("pathlib.Path.exists", return_value=False):
                result = run_avatar_gui()
                assert result == 2

    def test_creates_window_with_correct_params(self):
        """Test that webview window is created with correct parameters."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                run_avatar_gui(debug=True)
                
                mock_webview.create_window.assert_called_once()
                call_kwargs = mock_webview.create_window.call_args.kwargs
                
                assert call_kwargs["title"] == "Chatty Commander Avatar"
                assert call_kwargs["width"] == 800
                assert call_kwargs["height"] == 600
                assert call_kwargs["frameless"] is True
                assert call_kwargs["easy_drag"] is True
                assert call_kwargs["on_top"] is True
                assert call_kwargs["transparent"] is True

    def test_starts_webview_with_debug(self):
        """Test that webview starts with debug mode."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                run_avatar_gui(debug=True)
                
                mock_webview.start.assert_called_once()
                call_kwargs = mock_webview.start.call_args.kwargs
                assert call_kwargs["debug"] is True
                assert call_kwargs["http_server"] is False

    def test_returns_0_on_success(self):
        """Test returns 0 when window opens successfully."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                result = run_avatar_gui()
                assert result == 0

    def test_fallback_when_transparency_fails(self):
        """Test fallback window when transparency fails."""
        mock_webview = Mock()
        mock_webview.create_window.side_effect = [Exception("Transparency not supported"), None]
        mock_webview.start.side_effect = [Exception("First start failed"), None]
        
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                result = run_avatar_gui()
                
                # Should retry with fallback settings
                assert mock_webview.create_window.call_count == 2
                
                # Second call should have fallback params
                second_call = mock_webview.create_window.call_args_list[1]
                assert second_call.kwargs["frameless"] is False
                assert second_call.kwargs["on_top"] is False
                assert second_call.kwargs["transparent"] is False

    def test_returns_2_when_both_attempts_fail(self):
        """Test returns 2 when both transparency and fallback fail."""
        mock_webview = Mock()
        mock_webview.create_window.side_effect = Exception("Always fails")
        mock_webview.start.side_effect = Exception("Always fails")
        
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                result = run_avatar_gui()
                assert result == 2


class TestEdgeCases:
    """Edge case tests."""

    def test_debug_parameter_passed_through(self):
        """Test debug parameter is passed to webview.start."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                run_avatar_gui(debug=False)
                
                mock_webview.start.assert_called_with(debug=False, gui=None, http_server=False)

    def test_url_converted_to_file_uri(self):
        """Test that file path is converted to URI."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///absolute/path/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                run_avatar_gui()
                
                call_kwargs = mock_webview.create_window.call_args.kwargs
                assert call_kwargs["url"] == "file:///absolute/path/index.html"

    def test_window_dimensions_fixed(self):
        """Test that window dimensions are fixed at 800x600."""
        mock_webview = Mock()
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.resolve.return_value.as_uri.return_value = "file:///test/index.html"
        
        with patch("src.chatty_commander.avatars.avatar_gui.webview", mock_webview):
            with patch("src.chatty_commander.avatars.avatar_gui._avatar_index_path", return_value=mock_path):
                run_avatar_gui()
                
                call_kwargs = mock_webview.create_window.call_args.kwargs
                assert call_kwargs["width"] == 800
                assert call_kwargs["height"] == 600
