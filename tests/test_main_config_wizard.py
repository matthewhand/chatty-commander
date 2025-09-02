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
from unittest.mock import patch

from src.chatty_commander import main


def test_main_config_wizard(monkeypatch):
    """Ensure that invoking main with --config triggers ConfigCLI.run_wizard."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--config"])
    with (
        patch("config_cli.ConfigCLI.__init__", return_value=None),
        patch("config_cli.ConfigCLI.run_wizard") as mock_wizard,
        patch("src.chatty_commander.main.Config"),
        patch("src.chatty_commander.main.ModelManager"),
        patch("src.chatty_commander.main.StateManager"),
        patch("src.chatty_commander.main.CommandExecutor"),
        patch("src.chatty_commander.main.setup_logger"),
        patch(
            "src.chatty_commander.main.generate_default_config_if_needed",
            return_value=False,
        ),
    ):
        result = main.main()
        assert result == 0
        mock_wizard.assert_called_once()
