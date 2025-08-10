import unittest
from unittest.mock import patch, MagicMock

from src.chatty_commander.avatars.avatar_gui import run_avatar_gui


class TestAvatarGUI(unittest.TestCase):
    @patch('src.chatty_commander.avatars.avatar_gui.webview')
    def test_run_avatar_gui_creates_correct_window(self, mock_webview: MagicMock):
        """Ensure run_avatar_gui configures a transparent, frameless, always-on-top window."""
        # Arrange: mock webview API
        mock_webview.create_window = MagicMock()
        mock_webview.start = MagicMock(return_value=None)

        # Act
        rc = run_avatar_gui(debug=False)

        # Assert return code and API usage
        self.assertEqual(rc, 0)
        mock_webview.create_window.assert_called_once()
        _args, kwargs = mock_webview.create_window.call_args

        # We pass keyword args; verify key flags
        assert kwargs.get('frameless') is True
        assert kwargs.get('on_top') is True
        assert kwargs.get('transparent') is True
        assert kwargs.get('easy_drag') is True

        # Verify title and URL point to our avatar index.html
        assert kwargs.get('title') == 'Chatty Commander Avatar'
        url = kwargs.get('url')
        assert isinstance(url, str) and url.startswith('file://') and url.endswith('index.html')

        # And that start() is invoked
        mock_webview.start.assert_called_once()
