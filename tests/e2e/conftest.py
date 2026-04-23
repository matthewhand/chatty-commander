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

"""Playwright E2E test configuration with live server fixture."""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Generator
from typing import Any

import pytest

# Skip all E2E tests if playwright is not installed
try:
    from playwright.sync_api import Page, expect

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any  # type: ignore

pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright not installed. Run: pip install playwright && playwright install"
)


@pytest.fixture(scope="session")
def e2e_server() -> Generator[str, None, None]:
    """Start the FastAPI server for E2E tests.
    
    Yields the base URL for the running server.
    """
    import socket
    
    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    base_url = f"http://127.0.0.1:{port}"
    
    # Start server in no_auth mode for testing
    # Using the CLI web mode with --no-auth
    process = subprocess.Popen(
        [sys.executable, "-m", "chatty_commander", "web", "--port", str(port), "--no-auth"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/home/matthewh/chatty-commander"
    )
    
    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            import urllib.request
            urllib.request.urlopen(f"{base_url}/version", timeout=1)
            break
        except Exception:
            if i == max_retries - 1:
                process.terminate()
                raise RuntimeError(f"Server failed to start on {base_url}")
            time.sleep(0.5)
    
    yield base_url
    
    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def page(page: Page, e2e_server: str) -> Page:
    """Configure page with base URL."""
    page.goto(e2e_server)
    return page


@pytest.fixture
def version_page(page: Page, e2e_server: str) -> Page:
    """Navigate to version endpoint."""
    page.goto(f"{e2e_server}/version")
    return page


@pytest.fixture
def agents_page(page: Page, e2e_server: str) -> Page:
    """Navigate to agents endpoint."""
    page.goto(f"{e2e_server}/agents")
    return page


@pytest.fixture
def metrics_page(page: Page, e2e_server: str) -> Page:
    """Navigate to metrics endpoint."""
    page.goto(f"{e2e_server}/metrics")
    return page
