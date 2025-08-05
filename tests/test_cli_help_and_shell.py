import subprocess
import sys

PYTHON = sys.executable


def run_cmd(args, timeout=10):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_help_lists_key_flags():
    rc, out, err = run_cmd([PYTHON, 'main.py', '--help'])
    assert rc == 0
    text = out + err
    for token in ['--web', '--no-auth', '--port', '--gui', '--config', '--shell', '--log-level']:
        assert token in text, f"missing {token} in --help output"


def test_no_args_prints_intro_and_does_not_crash():
    rc, out, err = run_cmd([PYTHON, 'main.py', '--help'])
    assert rc == 0
    assert 'ChattyCommander' in (out + err)
