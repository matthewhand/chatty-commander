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

import os
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path
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
    
    handles = {"process": None, "server": None, "thread": None, "kind": None}
    
    # Start server in-process using the app directly (faster/more reliable than CLI subprocess for e2e)
    try:
        from chatty_commander.web.web_mode import create_app as _create_web_app
        import uvicorn
        from threading import Thread
        app = _create_web_app(no_auth=True)
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        thread = Thread(target=server.run, daemon=True)
        thread.start()
        handles["server"] = server
        handles["thread"] = thread
        handles["kind"] = "inproc"
    except Exception:
        # Fallback to subprocess (original behavior)
        project_root = str(Path(__file__).resolve().parents[2])
        env = os.environ.copy()
        env["PYTHONPATH"] = "src" + (":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        proc = subprocess.Popen(
            [sys.executable, "-m", "chatty_commander", "web", "--port", str(port), "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root,
            env=env
        )
        handles["process"] = proc
        handles["kind"] = "subprocess"
    
    # Wait for server to be ready (web init can be slow due to model/llm loads)
    max_retries = 90
    last_err = None
    for i in range(max_retries):
        try:
            import urllib.request
            urllib.request.urlopen(f"{base_url}/health", timeout=2)
            break
        except Exception as e:
            last_err = e
            if i == max_retries - 1:
                if handles["kind"] == "subprocess" and handles["process"]:
                    try:
                        handles["process"].terminate()
                        out, err = handles["process"].communicate(timeout=3)
                        diag = (err or out or b"").decode("utf-8", errors="replace")[-900:]
                    except Exception:
                        diag = "<no-diag>"
                else:
                    diag = "inproc-uvicorn (no extra diag)"
                raise RuntimeError(f"Server failed to start on {base_url} after {max_retries} tries. Last: {last_err}. Diag tail:\n{diag}") from e
            time.sleep(0.7)
    
    yield base_url
    
    # Cleanup
    if handles["kind"] == "subprocess" and handles["process"]:
        handles["process"].terminate()
        try:
            handles["process"].wait(timeout=5)
        except subprocess.TimeoutExpired:
            handles["process"].kill()
    elif handles["server"]:
        try:
            handles["server"].should_exit = True
            if handles["thread"]:
                handles["thread"].join(timeout=6)
        except Exception:
            pass


@pytest.fixture
def page(page: Page, e2e_server: str) -> Page:
    """Configure page with base URL (with domcontentloaded wait for stability)."""
    page.goto(e2e_server)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("body", timeout=8000)
    return page


@pytest.fixture
def version_page(page: Page, e2e_server: str) -> Page:
    """Navigate to version endpoint (with domcontentloaded wait for stability)."""
    page.goto(f"{e2e_server}/version")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("body", timeout=8000)
    return page


@pytest.fixture
def agents_page(page: Page, e2e_server: str) -> Page:
    """Navigate to agents endpoint (with domcontentloaded wait for stability)."""
    page.goto(f"{e2e_server}/agents")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("body", timeout=8000)
    return page


@pytest.fixture
def metrics_page(page: Page, e2e_server: str) -> Page:
    """Navigate to metrics endpoint (with domcontentloaded wait for stability)."""
    page.goto(f"{e2e_server}/metrics")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("body", timeout=8000)
    return page


# Screenshot capture helpers with categorization
@pytest.fixture
def screenshot_helper():
    """Helper fixture to capture screenshots during tests with user-guide categorization.
    
    Screenshots are organized by:
    - User guide section (getting-started, configuration, agents, etc.)
    - Operation type (normal-operation vs troubleshooting)
    """
    import os
    from pathlib import Path
    
    base_dir = Path(os.environ.get("SCREENSHOT_PATH", "e2e-screenshots"))
    
    # Define categories for user guide organization
    CATEGORIES = {
        # Getting Started - First time user flows
        "getting-started": ["login", "first-run", "welcome", "setup"],
        
        # Core Operations - Normal day-to-day usage
        "normal-operation": [
            "health-check", "version", "config-view", "config-update",
            "agents-list", "agent-create", "agent-edit", "commands-list",
            "metrics-dashboard", "system-info"
        ],
        
        # Configuration - Settings and customization
        "configuration": [
            "config-json", "environment-vars", "voice-settings", 
            "llm-backend", "web-port", "commands-custom"
        ],
        
        # Advanced Features - Power user workflows
        "advanced-features": [
            "websocket-realtime", "api-browser", "import-export",
            "batch-operations", "voice-control", "avatar-custom"
        ],
        
        # Troubleshooting - When things go wrong
        "troubleshooting": [
            "error-404", "error-500", "validation-fail", "auth-error",
            "connection-error", "timeout", "rate-limit", "health-fail"
        ],
        
        # Integration Testing - External connections
        "integration": [
            "ollama-connect", "openai-connect", "webhook-test",
            "bridge-event", "model-download", "voice-model-load"
        ],
    }
    
    class ScreenshotHelper:
        def __init__(self, base_directory: Path):
            self.base_directory = base_directory
            self.counters = {cat: 0 for cat in CATEGORIES.keys()}
            self.counters["uncategorized"] = 0
            
            # Create category directories
            for category in list(CATEGORIES.keys()) + ["uncategorized"]:
                cat_dir = self.base_directory / category
                cat_dir.mkdir(parents=True, exist_ok=True)
                # Create subdirs for normal vs troubleshooting
                if category not in ["troubleshooting", "getting-started"]:
                    (cat_dir / "normal").mkdir(exist_ok=True)
                    (cat_dir / "error").mkdir(exist_ok=True)
        
        def _categorize(self, name: str) -> tuple[str, str]:
            """Determine category and subcategory from screenshot name.
            
            Returns: (category, subcategory) where subcategory is 'normal' or 'error'
            """
            name_lower = name.lower()
            
            # Check if it's an error/troubleshooting scenario
            is_error = any(err in name_lower for err in [
                "error", "fail", "timeout", "invalid", "unauthorized",
                "forbidden", "not-found", "bad-request", "server-error",
                "connection-refused", "health-fail"
            ])
            
            # Find matching category
            for category, keywords in CATEGORIES.items():
                if any(kw in name_lower for kw in keywords):
                    subcategory = "error" if is_error else "normal"
                    return category, subcategory
            
            # Default to uncategorized
            subcategory = "error" if is_error else "normal"
            return "uncategorized", subcategory
        
        def capture(self, page, name: str, category: str = None) -> str:
            """Capture a screenshot with automatic categorization.
            
            Args:
                page: Playwright page object
                name: Screenshot name (will be used for categorization)
                category: Optional explicit category override
            
            Returns:
                Path to saved screenshot
            """
            # Determine category
            if category is None:
                category, subcategory = self._categorize(name)
            else:
                subcategory = "normal"  # Explicit category = normal flow
            
            # Update counter
            self.counters[category] += 1
            counter = self.counters[category]
            
            # Build path: e2e-screenshots/{category}/{subcategory}/{counter}-{name}.png
            if category == "uncategorized" or category == "troubleshooting":
                # Troubleshooting and uncategorized go directly in category dir
                filepath = self.base_directory / category / f"{counter:03d}-{name}.png"
            else:
                # Other categories have normal/error subdirectories
                filepath = self.base_directory / category / subcategory / f"{counter:03d}-{name}.png"
            
            # Capture screenshot
            page.screenshot(path=str(filepath), full_page=True)
            
            # Log with emoji indicators
            emoji = "❌" if subcategory == "error" else "✅"
            guide_type = "TROUBLESHOOTING" if subcategory == "error" else "USER GUIDE"
            print(f"{emoji} [{guide_type}] [{category}] Screenshot: {filepath.name}")
            
            return str(filepath)
        
        def capture_guide(self, page, section: str, step: str) -> str:
            """Capture screenshot specifically for user guide documentation.
            
            Args:
                page: Playwright page object
                section: User guide section (e.g., "getting-started", "configuration")
                step: Step description for filename
            
            Returns:
                Path to saved screenshot
            """
            return self.capture(page, f"{section}-{step}", category=section)
        
        def capture_troubleshooting(self, page, issue: str, context: str = "") -> str:
            """Capture screenshot for troubleshooting documentation.
            
            Args:
                page: Playwright page object  
                issue: Issue being demonstrated (e.g., "connection-timeout")
                context: Additional context for filename
            
            Returns:
                Path to saved screenshot
            """
            name = f"{issue}-{context}" if context else issue
            return self.capture(page, name, category="troubleshooting")
        
        def get_summary(self) -> dict:
            """Get summary of captured screenshots by category."""
            summary = {}
            for category in list(CATEGORIES.keys()) + ["uncategorized"]:
                cat_dir = self.base_directory / category
                if cat_dir.exists():
                    screenshots = list(cat_dir.rglob("*.png"))
                    summary[category] = len(screenshots)
            return summary
    
    return ScreenshotHelper(base_dir)


@pytest.fixture
def live_server():
    """Start the actual application server for HTTP-based E2E tests (in-process preferred).
    
    Uses the same robust pattern as e2e_server for speed and reliability.
    """
    import socket
    import time
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    base_url = f"http://127.0.0.1:{port}"
    
    handles = {"process": None, "server": None, "thread": None, "kind": None}
    
    try:
        from chatty_commander.web.web_mode import create_app as _create_web_app
        import uvicorn
        from threading import Thread
        import requests  # for polling
        
        app = _create_web_app(no_auth=True)
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        thread = Thread(target=server.run, daemon=True)
        thread.start()
        handles["server"] = server
        handles["thread"] = thread
        handles["kind"] = "inproc"
    except Exception:
        # Fallback to subprocess (legacy CLI form)
        import subprocess
        project_root = str(Path(__file__).resolve().parents[2])
        env = os.environ.copy()
        env["PYTHONPATH"] = "src" + (":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        proc = subprocess.Popen(
            [sys.executable, "-m", "chatty_commander", "web",
             "--port", str(port), "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root,
            env=env
        )
        handles["process"] = proc
        handles["kind"] = "subprocess"
    
    max_retries = 60
    last_err = None
    for i in range(max_retries):
        try:
            import requests
            resp = requests.get(f"{base_url}/health", timeout=2)
            if resp.status_code == 200:
                break
        except Exception as e:
            last_err = e
            if i == max_retries - 1:
                if handles["kind"] == "subprocess" and handles["process"]:
                    try:
                        handles["process"].terminate()
                        out, err = handles["process"].communicate(timeout=3)
                        diag = (err or out or b"").decode("utf-8", errors="replace")[-800:]
                    except Exception:
                        diag = "<no-diag>"
                else:
                    diag = "inproc"
                raise RuntimeError(f"Server failed to start on {base_url} after retries. Last: {last_err}. Diag: {diag}") from e
            time.sleep(0.6)
    
    yield base_url
    
    if handles["kind"] == "subprocess" and handles["process"]:
        handles["process"].terminate()
        try:
            handles["process"].wait(timeout=5)
        except subprocess.TimeoutExpired:
            handles["process"].kill()
    elif handles["server"]:
        try:
            handles["server"].should_exit = True
            if handles["thread"]:
                handles["thread"].join(timeout=5)
        except Exception:
            pass


# Auto-capture screenshot on test failure
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot when a test fails (if using Playwright)."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Try to capture screenshot if page fixture was used
        page = item.funcargs.get("page")
        if page and PLAYWRIGHT_AVAILABLE:
            try:
                screenshots_dir = Path("e2e-screenshots")
                screenshots_dir.mkdir(exist_ok=True)
                filename = f"FAILED-{item.name}.png"
                filepath = screenshots_dir / filename
                page.screenshot(path=str(filepath), full_page=True)
                print(f"\n📸 Failure screenshot saved: {filepath}")
                
                # Add to report
                if hasattr(report, "extras"):
                    report.extras.append(f"Screenshot: {filepath}")
            except Exception as e:
                print(f"\n⚠️ Failed to capture screenshot: {e}")
