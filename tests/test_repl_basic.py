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
import textwrap

PYTHON = sys.executable


def run_with_stdin(args, input_text: str, timeout=15):
    env = os.environ.copy()
    env.pop("DISPLAY", None)
    proc = subprocess.run(
        args, input=input_text, capture_output=True, text=True, timeout=timeout, env=env
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_repl_quick_session_executes_and_exits_cleanly():
    # Start shell mode, execute a trivial command, then exit without hanging.
    # Assumes: `python main.py --shell` starts an interactive REPL reading from stdin.
    script = textwrap.dedent(
        """
        help
        exit
        """
    )
    rc, out, err = run_with_stdin(
        [PYTHON, "src/chatty_commander/main.py", "--shell"], script, timeout=15
    )
    assert rc == 0
    combined = (out or "") + (err or "")
    # Loosely assert presence of help/prompt tokens without being brittle across implementations.
    assert (
        ("help" in combined.lower())
        or ("exit" in combined.lower())
        or (">>> " in combined)
    )
