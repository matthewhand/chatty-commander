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

import httpx
import pytest
import respx

from chatty_commander.app.config import Config
from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool
from chatty_commander.tools.browser_analyst import AnalystRequest, summarize_url


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    """Mock config so we have a known state without domain restrictions."""
    mock_data = {
        "advisors": {
            "browser_analyst": {
                "allowlist": None
            }
        }
    }
    def mock_init(self, *args, **kwargs):
        self.config_data = mock_data
    monkeypatch.setattr(Config, "__init__", mock_init)


@respx.mock
def test_summarize_url_success():
    html_content = """
    <html>
      <head><title>Test Page</title></head>
      <body>
        <script>var x = 1;</script>
        <h1>Hello World</h1>
        <p>This is a test paragraph with <b>bold</b> text.</p>
        <div>""" + ("A" * 600) + """</div>
      </body>
    </html>
    """
    respx.get("https://example.com/test").mock(return_value=httpx.Response(200, text=html_content))

    req = AnalystRequest(url="https://example.com/test")
    result = summarize_url(req)

    assert result.title == "Test Page"
    assert "Hello World" in result.summary
    assert "This is a test paragraph with bold text." in result.summary
    assert "var x = 1" not in result.summary
    assert len(result.summary) == 500
    assert result.url == "https://example.com/test"


@respx.mock
def test_summarize_url_fallback():
    respx.get("https://example.com/error").mock(side_effect=httpx.ConnectError("Network error"))

    req = AnalystRequest(url="https://example.com/error")
    result = summarize_url(req)

    assert result.title == "Error"
    assert "Failed to fetch: Network error" in result.summary
    assert result.url == "https://example.com/error"


@respx.mock
def test_browser_analyst_tool_success():
    html_content = "<html><head><title>Tool Page</title></head><body><p>Tool content</p></body></html>"
    respx.get("https://github.com/mhand").mock(return_value=httpx.Response(200, text=html_content))

    result = browser_analyst_tool("https://github.com/mhand")

    assert "Title: Tool Page" in result
    assert "Summary: Tool content" in result or "Tool content" in result


@respx.mock
def test_browser_analyst_tool_fallback():
    respx.get("https://github.com/error").mock(side_effect=httpx.ConnectError("Network error"))

    result = browser_analyst_tool("https://github.com/error")

    assert "Unable to analyze" in result
    assert "Network error" in result

    respx.get("https://stackoverflow.com/error").mock(side_effect=httpx.ConnectError("Network error"))
    result_so = browser_analyst_tool("https://stackoverflow.com/error")
    assert "Unable to analyze" in result_so

    respx.get("https://example.com/error").mock(side_effect=httpx.ConnectError("Network error"))
    result_ex = browser_analyst_tool("https://example.com/error")
    assert "Unable to analyze" in result_ex


def test_allowlist_blocking(monkeypatch):
    """Test that URLs not in the allowlist are blocked."""
    mock_data = {
        "advisors": {
            "browser_analyst": {
                "allowlist": ["allowed.com"]
            }
        }
    }
    def mock_init(self, *args, **kwargs):
        self.config_data = mock_data
    monkeypatch.setattr(Config, "__init__", mock_init)

    # test summarize_url
    req = AnalystRequest(url="https://blocked.com/page")
    result = summarize_url(req)
    assert result.title == "Error"
    assert result.summary == "Domain not allowed."

    # test browser_analyst_tool
    result_tool = browser_analyst_tool("https://blocked.com/page")
    assert "Error: Domain blocked.com is not allowed." in result_tool


def test_allowlist_empty_blocking(monkeypatch):
    """Test that an empty allowlist blocks all URLs."""
    mock_data = {
        "advisors": {
            "browser_analyst": {
                "allowlist": []
            }
        }
    }
    def mock_init(self, *args, **kwargs):
        self.config_data = mock_data
    monkeypatch.setattr(Config, "__init__", mock_init)

    req = AnalystRequest(url="https://example.com/page")
    result = summarize_url(req)
    assert result.title == "Error"
    assert result.summary == "Domain not allowed."

    result_tool = browser_analyst_tool("https://example.com/page")
    assert "Error: Domain example.com is not allowed." in result_tool
