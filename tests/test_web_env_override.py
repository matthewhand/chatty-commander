#!/usr/bin/env python3
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
        s.bind(("", 0))
        port = s.getsockname()[1]

    env = os.environ.copy()
    env["CHATCOMM_HOST"] = "127.0.0.1"
    env["CHATCOMM_PORT"] = str(port)
    env["CHATCOMM_LOG_LEVEL"] = "warning"
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

    cmd = [sys.executable, "-m", "chatty_commander.main", "--web", "--no-auth"]
    proc = subprocess.Popen(
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
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
            raise AssertionError(
                f"Server did not start\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            )
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
    assert resp is not None and resp.status_code == 200
