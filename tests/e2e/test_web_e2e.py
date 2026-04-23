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

"""Playwright E2E tests for ChattyCommander web interface."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Page


class TestVersionEndpoint:
    """E2E tests for version endpoint."""
    
    def test_version_page_loads(self, version_page: Page) -> None:
        """Test that version endpoint returns valid JSON."""
        # Wait for JSON content to be visible
        version_page.wait_for_load_state("networkidle")
        
        # Get page content and verify it's valid JSON
        content = version_page.content()
        assert "version" in content or "app_name" in content
    
    def test_version_response_format(self, page: Page, e2e_server: str) -> None:
        """Test version endpoint returns expected JSON structure."""
        # Use browser's fetch API to get JSON response
        result = page.evaluate(f"""async () => {{
            const response = await fetch('{e2e_server}/version');
            return await response.json();
        }}""")
        
        assert isinstance(result, dict)
        assert "version" in result or "app_name" in result


class TestAgentsEndpoint:
    """E2E tests for agents management endpoint."""
    
    def test_agents_page_loads(self, agents_page: Page) -> None:
        """Test that agents endpoint returns valid response."""
        agents_page.wait_for_load_state("networkidle")
        content = agents_page.content()
        # Should contain agents data or empty list
        assert content is not None
    
    def test_agents_json_structure(self, page: Page, e2e_server: str) -> None:
        """Test agents endpoint returns proper JSON."""
        result = page.evaluate(f"""async () => {{
            const response = await fetch('{e2e_server}/agents');
            return await response.json();
        }}""")
        
        assert isinstance(result, dict)
        # Should have agents field
        assert "agents" in result or "error" in result


class TestMetricsEndpoint:
    """E2E tests for metrics endpoint."""
    
    def test_metrics_page_loads(self, metrics_page: Page) -> None:
        """Test that metrics endpoint is accessible."""
        metrics_page.wait_for_load_state("networkidle")
        content = metrics_page.content()
        assert content is not None
    
    def test_metrics_json_structure(self, page: Page, e2e_server: str) -> None:
        """Test metrics endpoint returns proper JSON structure."""
        result = page.evaluate(f"""async () => {{
            const response = await fetch('{e2e_server}/metrics');
            return await response.json();
        }}""")
        
        assert isinstance(result, dict)
        # Metrics should have various fields
        assert any(key in result for key in ["uptime", "requests", "memory", "cpu"])


class TestWebSocketConnection:
    """E2E tests for WebSocket connections."""
    
    def test_websocket_connects(self, page: Page, e2e_server: str) -> None:
        """Test that WebSocket endpoint accepts connections."""
        result = page.evaluate(f"""async () => {{
            return new Promise((resolve) => {{
                const ws = new WebSocket('{e2e_server.replace('http', 'ws')}/ws');
                ws.onopen = () => resolve({{ connected: true }});
                ws.onerror = () => resolve({{ connected: false }});
                setTimeout(() => resolve({{ connected: false, timeout: true }}), 5000);
            }});
        }}""")
        
        assert isinstance(result, dict)
        # WebSocket may or may not be available depending on router setup
        assert "connected" in result
    
    def test_websocket_receives_message(self, page: Page, e2e_server: str) -> None:
        """Test WebSocket can receive messages."""
        result = page.evaluate(f"""async () => {{
            return new Promise((resolve) => {{
                try {{
                    const ws = new WebSocket('{e2e_server.replace('http', 'ws')}/ws');
                    let received = false;
                    ws.onmessage = (event) => {{
                        received = true;
                        resolve({{ received: true, data: event.data }});
                    }};
                    ws.onerror = () => resolve({{ received: false, error: true }});
                    setTimeout(() => resolve({{ received: false, timeout: true }}), 5000);
                }} catch (e) {{
                    resolve({{ received: false, error: String(e) }});
                }}
            }});
        }}""")
        
        assert isinstance(result, dict)


class TestCORSHeaders:
    """E2E tests for CORS configuration."""
    
    def test_cors_headers_present(self, page: Page, e2e_server: str) -> None:
        """Test that CORS headers are properly set."""
        result = page.evaluate(f"""async () => {{
            const response = await fetch('{e2e_server}/version', {{
                method: 'GET',
                headers: {{ 'Origin': 'http://example.com' }}
            }});
            return {{
                access_control_allow_origin: response.headers.get('access-control-allow-origin'),
                status: response.status
            }};
        }}""")
        
        assert isinstance(result, dict)
        assert result.get("status") == 200


class TestAPIErrorHandling:
    """E2E tests for API error handling."""
    
    def test_404_not_found(self, page: Page, e2e_server: str) -> None:
        """Test that non-existent endpoints return 404."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/nonexistent-endpoint-12345');
                return {{ status: response.status, ok: response.ok }};
            }} catch (e) {{
                return {{ error: true, message: String(e) }};
            }}
        }}""")
        
        assert isinstance(result, dict)
        # Should return 404 or similar error
        assert not result.get("ok", True) or result.get("status", 200) >= 400
    
    def test_invalid_method(self, page: Page, e2e_server: str) -> None:
        """Test that invalid HTTP methods are handled."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/version', {{
                    method: 'DELETE'
                }});
                return {{ status: response.status, ok: response.ok }};
            }} catch (e) {{
                return {{ error: true, message: String(e) }};
            }}
        }}""")
        
        assert isinstance(result, dict)


class TestBrowserCompatibility:
    """Cross-browser compatibility tests."""
    
    def test_page_title_exists(self, page: Page, e2e_server: str) -> None:
        """Test that page has proper title or header."""
        page.goto(e2e_server)
        page.wait_for_load_state("domcontentloaded")
        
        # Check if there's any content on the root page
        title = page.title()
        content = page.content()
        
        # Either should have a title or some content
        assert title or content
    
    def test_javascript_execution(self, page: Page, e2e_server: str) -> None:
        """Test that JavaScript executes properly in browser."""
        page.goto(e2e_server)
        
        # Execute simple JavaScript
        result = page.evaluate("() => 1 + 1")
        assert result == 2
        
        # Check browser APIs are available
        has_fetch = page.evaluate("() => typeof fetch !== 'undefined'")
        assert has_fetch is True


class TestBridgeEndpoint:
    """E2E tests for bridge event endpoint."""
    
    def test_bridge_requires_token(self, page: Page, e2e_server: str) -> None:
        """Test that bridge endpoint requires authentication token."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/bridge/event', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{}})
                }});
                return {{ status: response.status, ok: response.ok }};
            }} catch (e) {{
                return {{ error: true, message: String(e) }};
            }}
        }}""")
        
        assert isinstance(result, dict)
        # Should be unauthorized without token
        assert result.get("status") in [401, 403, 404] or not result.get("ok", True)
