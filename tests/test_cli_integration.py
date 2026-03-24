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

import sys
import types
from unittest.mock import MagicMock, patch

# Patch sys.modules to mock openwakeword for imports
sys.modules["openwakeword"] = types.ModuleType("openwakeword")
mock_model_mod = types.ModuleType("openwakeword.model")
mock_model_mod.Model = type("Model", (), {})
sys.modules["openwakeword.model"] = mock_model_mod

from chatty_commander.cli.cli import cli_main  # noqa: E402


def test_cli_help(monkeypatch, capsys):
    """Test that --help prints usage and exits with 0."""
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--help"])
    ret = cli_main()
    assert ret == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out or "usage:" in captured.err
    assert "ChattyCommander" in captured.out


def test_cli_web_mode(monkeypatch):
    """Test that --web launches web mode."""
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--web", "--no-auth"])

    with patch("chatty_commander.cli.cli.run_web_mode") as mock_web:
        cli_main()
        mock_web.assert_called_once()
        # Verify call args if needed
        args, kwargs = mock_web.call_args
        assert kwargs.get("no_auth") is True


def test_cli_gui_mode(monkeypatch):
    """Test that --gui launches gui mode."""
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--gui", "--no-gui"])

    with patch("chatty_commander.cli.cli.run_gui_mode") as mock_gui:
        cli_main()
        mock_gui.assert_called_once()
        args, kwargs = mock_gui.call_args
        assert kwargs.get("no_gui") is True


def test_cli_config_wizard(monkeypatch):
    """Test that --config launches config wizard."""
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--config"])

    # Mock ConfigCLI class content within the function import
    mock_config_cli_cls = MagicMock()
    mock_instance = mock_config_cli_cls.return_value

    # We need to patch where it's imported FROM or patch sys.modules
    with patch.dict(sys.modules, {"chatty_commander.config_cli": MagicMock(ConfigCLI=mock_config_cli_cls)}):
        cli_main()
        mock_config_cli_cls.assert_called()
        mock_instance.run_wizard.assert_called_once()


def test_cli_interactive_shell(monkeypatch):
    """Test that running with no args starts interactive shell."""
    monkeypatch.setattr(sys, "argv", ["chatty-commander"])

    with patch("chatty_commander.cli.cli.run_interactive_shell") as mock_shell:
        cli_main()
        mock_shell.assert_called_once()
