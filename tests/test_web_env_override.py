#!/usr/bin/env python3
"""Test that web server respects environment variable overrides."""

import os
import subprocess
import sys
import time

import requests


def test_web_server_env_overrides():
    import socket

    # Find an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]

    env = os.environ.copy()
    env["CHATCOMM_HOST"] = "127.0.0.1"
    env["CHATCOMM_PORT"] = str(port)
    env["CHATCOMM_LOG_LEVEL"] = "warning"
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

    cmd = [sys.executable, "-m", "chatty_commander.main", "--web", "--no-auth"]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    url = f"http://127.0.0.1:{port}/api/v1/health"
    resp = None
    try:
        for _ in range(30):
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            stdout, stderr = proc.communicate(timeout=1)
            raise AssertionError(f"Server did not start\nSTDOUT: {stdout}\nSTDERR: {stderr}")
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
    assert resp is not None and resp.status_code == 200
