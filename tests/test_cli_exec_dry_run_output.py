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

import io
import sys

from src.chatty_commander.cli.cli import cli_main


def test_cli_exec_dry_run_prints_action(monkeypatch):
    # Patch Config to return a known model_actions mapping
    import chatty_commander.app.config as config_module
    from src.chatty_commander.cli import cli as cli_module

    class DummyCfg:
        def __init__(self):
            self.model_actions = {"hello": {"shell": {"cmd": "echo hi"}}}

    # Patch both the config module and the _resolve_Config function
    monkeypatch.setattr(config_module, "Config", DummyCfg)
    monkeypatch.setattr(cli_module, "_resolve_Config", lambda: DummyCfg)

    # Simulate CLI invocation
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "exec", "hello", "--dry-run"])

    stdout = io.StringIO()
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    try:
        cli_main()
    except SystemExit as e:
        assert e.code in (0, None)

    out = stdout.getvalue()
    assert "DRY RUN: would execute command 'hello'" in out
