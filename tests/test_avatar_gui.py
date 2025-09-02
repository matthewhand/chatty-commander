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

import unittest
from unittest.mock import MagicMock, patch

from chatty_commander.avatars.avatar_gui import run_avatar_gui


class TestAvatarGUI(unittest.TestCase):
    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_run_avatar_gui_creates_correct_window(self, mock_webview: MagicMock):
        """Ensure run_avatar_gui configures a transparent, frameless, always-on-top window."""
        mock_webview.create_window = MagicMock()
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 0)
        mock_webview.create_window.assert_called_once()
        _args, kwargs = mock_webview.create_window.call_args
        assert kwargs.get("frameless") is True
        assert kwargs.get("on_top") is True
        assert kwargs.get("transparent") is True
        assert kwargs.get("easy_drag") is True
        assert kwargs.get("title") == "Chatty Commander Avatar"
        url = kwargs.get("url")
        assert (
            isinstance(url, str)
            and url.startswith("file://")
            and url.endswith("index.html")
        )
        mock_webview.start.assert_called_once()

    @patch("chatty_commander.avatars.avatar_gui.webview", None)
    def test_run_avatar_gui_missing_pywebview(self):
        """If pywebview is not installed, we return code 2 and do not crash."""
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 2)

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_run_avatar_gui_missing_index(self, mock_webview: MagicMock):
        """If the index.html cannot be found, we return 2 and do not call webview APIs."""
        from pathlib import Path

        with patch(
            "chatty_commander.avatars.avatar_gui._avatar_index_path",
            return_value=Path("does/not/exist.html"),
        ):
            rc = run_avatar_gui(debug=False)
            self.assertEqual(rc, 2)
            mock_webview.create_window.assert_not_called()
            mock_webview.start.assert_not_called()

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_run_avatar_gui_transparency_fallback_then_success(
        self, mock_webview: MagicMock
    ):
        """If transparent window fails, we retry without transparency and succeed."""
        # First call raises, second call succeeds
        calls = {"i": 0}

        def create_window_side_effect(*args, **kwargs):
            calls["i"] += 1
            if calls["i"] == 1:
                raise RuntimeError("no transparency support")
            return None

        mock_webview.create_window = MagicMock(side_effect=create_window_side_effect)
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 0)
        assert mock_webview.create_window.call_count == 2
        mock_webview.start.assert_called_once()

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_run_avatar_gui_total_failure(self, mock_webview: MagicMock):
        """If both attempts to create a window fail, we return 2."""
        mock_webview.create_window = MagicMock(side_effect=RuntimeError("boom"))
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 2)
        # start should not be called if window creation always fails
        mock_webview.start.assert_not_called()
