import subprocess
import sys

PYTHON = sys.executable


def run_cmd(args, timeout=10):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_help_includes_examples_section():
    rc, out, err = run_cmd([PYTHON, 'src/chatty_commander/main.py', '--help'])
    assert rc == 0
    text = (out or '') + (err or '')
    assert 'Examples:' in text
