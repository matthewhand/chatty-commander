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
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_help_lists_key_flags():
    rc, out, err = run_cmd([PYTHON, 'src/chatty_commander/main.py', '--help'])
    assert rc == 0
    text = out + err
    for token in ['--web', '--no-auth', '--port', '--gui', '--config', '--shell', '--log-level']:
        assert token in text, f"missing {token} in --help output"


def test_no_args_prints_intro_and_does_not_crash():
    rc, out, err = run_cmd([PYTHON, 'src/chatty_commander/main.py'])
    assert rc == 0
    text = out + err
    assert "ChattyCommander - Voice Command System" in text
    assert "Use --help for available options" in text
