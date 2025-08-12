import subprocess
import sys
import textwrap

PYTHON = sys.executable


def run_with_stdin(args, input_text: str, timeout=15):
    proc = subprocess.run(args, input=input_text, capture_output=True, text=True, timeout=timeout)
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
        [PYTHON, 'src/chatty_commander/main.py', '--shell'], script, timeout=15
    )
    assert rc == 0
    combined = (out or '') + (err or '')
    # Loosely assert presence of help/prompt tokens without being brittle across implementations.
    assert ('help' in combined.lower()) or ('exit' in combined.lower()) or ('>>> ' in combined)
