import httpx
import pytest
import respx

from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool
from chatty_commander.app.config import Config
from chatty_commander.utils.url_validator import PinnedURL


@pytest.fixture(autouse=True)
def stub_resolution(monkeypatch):
    """Pin URLs to themselves: no real DNS in tests, and the fetched URL
    stays the hostname URL so respx routes match. The IP-pinning behaviour
    itself is covered by tests/test_url_validator_rebinding.py."""

    def fake_resolve(url):
        from urllib.parse import urlparse

        host = urlparse(url).hostname or ""
        return PinnedURL(url=url, ip="203.0.113.10", host_header=host, sni_hostname=host)

    monkeypatch.setattr(
        "chatty_commander.advisors.tools.browser_analyst.resolve_safe_url",
        fake_resolve,
    )


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

    result_tool = browser_analyst_tool("https://example.com/page")
    assert "Error: Domain example.com is not allowed." in result_tool
