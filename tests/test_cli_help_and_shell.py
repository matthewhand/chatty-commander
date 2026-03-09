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

import os
import subprocess
import sys

PYTHON = sys.executable


def run_cmd(args, timeout=10):
    """Run a command in a clean environment and capture output."""
    env = os.environ.copy()
    # Some tests set DISPLAY which can cause headless runs to fail when
    # downstream libraries (e.g., pyautogui) try to connect to an X server.
    env.pop("DISPLAY", None)
    proc = subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, env=env
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_help_lists_key_flags():
    rc, out, err = run_cmd([PYTHON, "-m", "chatty_commander.main", "--help"])
    assert rc == 0
    text = out + err
    for token in [
        "--web",
        "--no-auth",
        "--port",
        "--gui",
        "--config",
        "--shell",
        "--log-level",
    ]:
        assert token in text, f"missing {token} in --help output"


def test_no_args_prints_intro_and_does_not_crash():
    rc, out, err = run_cmd([PYTHON, "-m", "chatty_commander.main"])
    assert rc == 0
    text = out + err
    assert "ChattyCommander - Voice Command System" in text
    assert "Starting interactive shell" in text
