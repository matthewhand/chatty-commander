import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from chatty_commander.app.config import Config

class TestConfigAutostart(unittest.TestCase):
    def setUp(self):
        # Prevent actual file loading issues
        with patch('builtins.open', side_effect=FileNotFoundError):
             self.config = Config(config_file="dummy.json")

        # Mock logger to avoid clutter
        self.logger_patcher = patch('chatty_commander.app.config.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self.logger_patcher.stop()

    @patch('sys.platform', 'linux')
    @patch('pathlib.Path.home')
    def test_enable_start_on_boot_linux(self, mock_home):
        mock_path = MagicMock()
        # Ensure path concatenation returns a mock that can handle further concatenation
        mock_home.return_value = mock_path
        autostart_dir = mock_path / ".config" / "autostart"
        desktop_file = autostart_dir / "chattycommander.desktop"

        # We need to ensure mkdir doesn't fail
        autostart_dir.mkdir.return_value = None

        # Mock _get_startup_command
        with patch.object(self.config, '_get_startup_command', return_value='/usr/bin/chatty-commander --gui'):
            self.config._enable_start_on_boot()

        autostart_dir.mkdir.assert_called_with(parents=True, exist_ok=True)
        desktop_file.write_text.assert_called()
        content = desktop_file.write_text.call_args[0][0]
        self.assertIn("Exec=/usr/bin/chatty-commander --gui", content)
        self.assertIn("Name=ChattyCommander", content)

    @patch('sys.platform', 'linux')
    @patch('pathlib.Path.home')
    def test_disable_start_on_boot_linux(self, mock_home):
        mock_path = MagicMock()
        mock_home.return_value = mock_path
        # Setup the path chain
        desktop_file = mock_path / ".config" / "autostart" / "chattycommander.desktop"
        desktop_file.exists.return_value = True

        self.config._disable_start_on_boot()

        desktop_file.unlink.assert_called_once()

    @patch('sys.platform', 'darwin')
    @patch('pathlib.Path.home')
    def test_enable_start_on_boot_macos(self, mock_home):
        mock_path = MagicMock()
        mock_home.return_value = mock_path
        launch_agents_dir = mock_path / "Library" / "LaunchAgents"
        plist_file = launch_agents_dir / "com.chattycommander.startup.plist"

        with patch.object(self.config, '_get_startup_command', return_value='/usr/bin/chatty-commander --gui'):
            self.config._enable_start_on_boot()

        launch_agents_dir.mkdir.assert_called_with(parents=True, exist_ok=True)
        plist_file.write_text.assert_called()
        content = plist_file.write_text.call_args[0][0]
        self.assertIn("<string>/usr/bin/chatty-commander --gui</string>", content)

    @patch('sys.platform', 'darwin')
    @patch('pathlib.Path.home')
    def test_disable_start_on_boot_macos(self, mock_home):
        mock_path = MagicMock()
        mock_home.return_value = mock_path
        plist_file = mock_path / "Library" / "LaunchAgents" / "com.chattycommander.startup.plist"
        plist_file.exists.return_value = True

        self.config._disable_start_on_boot()

        plist_file.unlink.assert_called_once()

    @patch('sys.platform', 'win32')
    def test_enable_start_on_boot_windows(self):
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        mock_winreg.REG_SZ = 3

        with patch.dict(sys.modules, {'winreg': mock_winreg}):
            with patch.object(self.config, '_get_startup_command', return_value='"C:\\App.exe" --gui'):
                self.config._enable_start_on_boot()

        mock_winreg.OpenKey.assert_called_with(1, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, 2)
        mock_winreg.SetValueEx.assert_called()
        args = mock_winreg.SetValueEx.call_args[0]
        self.assertEqual(args[1], "ChattyCommander")
        self.assertEqual(args[4], '"C:\\App.exe" --gui')
        mock_winreg.CloseKey.assert_called()

    @patch('sys.platform', 'win32')
    def test_disable_start_on_boot_windows(self):
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2

        with patch.dict(sys.modules, {'winreg': mock_winreg}):
            self.config._disable_start_on_boot()

        mock_winreg.OpenKey.assert_called()
        mock_winreg.DeleteValue.assert_called_with(mock_winreg.OpenKey.return_value, "ChattyCommander")
        mock_winreg.CloseKey.assert_called()

    @patch('shutil.which')
    @patch('sys.executable', '/usr/bin/python3')
    def test_get_startup_command_frozen(self, mock_which):
        with patch('sys.frozen', True, create=True):
             cmd = self.config._get_startup_command()
             self.assertEqual(cmd, '"/usr/bin/python3" --gui')

    @patch('shutil.which')
    @patch('sys.executable', '/usr/bin/python3')
    def test_get_startup_command_installed(self, mock_which):
        # We must ensure frozen is false (default), but to be safe
        with patch('sys.frozen', False, create=True):
            mock_which.return_value = "/usr/bin/chatty-commander"
            cmd = self.config._get_startup_command()
            self.assertEqual(cmd, '"/usr/bin/chatty-commander" --gui')

    @patch('shutil.which')
    @patch('sys.executable', '/usr/bin/python3')
    def test_get_startup_command_fallback(self, mock_which):
        with patch('sys.frozen', False, create=True):
            mock_which.return_value = None
            cmd = self.config._get_startup_command()
            self.assertEqual(cmd, '"/usr/bin/python3" -m chatty_commander.cli.cli --gui')
