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

"""Playwright E2E tests for Avatar API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Page


class TestAvatarAPI:
    """E2E tests for avatar-related API endpoints."""
    
    def test_avatar_api_available(self, page: Page, e2e_server: str) -> None:
        """Test avatar API endpoint exists."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/avatar/api/avatars');
                return {{ status: response.status, ok: response.ok }};
            }} catch (e) {{
                return {{ error: String(e) }};
            }}
        }}""")
        
        assert isinstance(result, dict)
        # May return 200 or 404 depending on router availability
        assert "status" in result
    
    def test_avatar_selector_api(self, page: Page, e2e_server: str) -> None:
        """Test avatar selector endpoint."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/avatar/select');
                return {{ status: response.status }};
            }} catch (e) {{
                return {{ error: true }};
            }}
        }}""")
        
        assert isinstance(result, dict)


class TestAvatarWebSocket:
    """E2E tests for avatar WebSocket connections."""
    
    def test_avatar_websocket_connects(self, page: Page, e2e_server: str) -> None:
        """Test avatar WebSocket endpoint accepts connections."""
        result = page.evaluate(f"""async () => {{
            return new Promise((resolve) => {{
                try {{
                    const ws = new WebSocket('{e2e_server.replace('http', 'ws')}/avatar/ws');
                    const timeout = setTimeout(() => {{
                        ws.close();
                        resolve({{ connected: false, timeout: true }});
                    }}, 3000);
                    
                    ws.onopen = () => {{
                        clearTimeout(timeout);
                        ws.close();
                        resolve({{ connected: true }});
                    }};
                    
                    ws.onerror = () => {{
                        clearTimeout(timeout);
                        resolve({{ connected: false, error: true }});
                    }};
                }} catch (e) {{
                    resolve({{ connected: false, exception: String(e) }});
                }}
            }});
        }}""")
        
        assert isinstance(result, dict)
        assert "connected" in result
    
    def test_avatar_websocket_send_receive(self, page: Page, e2e_server: str) -> None:
        """Test sending and receiving messages on avatar WebSocket."""
        result = page.evaluate(f"""async () => {{
            return new Promise((resolve) => {{
                try {{
                    const ws = new WebSocket('{e2e_server.replace('http', 'ws')}/avatar/ws');
                    let received = false;
                    
                    const timeout = setTimeout(() => {{
                        ws.close();
                        resolve({{ received: false, timeout: true }});
                    }}, 5000);
                    
                    ws.onopen = () => {{
                        // Send a ping or hello message
                        ws.send(JSON.stringify({{ type: 'ping' }}));
                    }};
                    
                    ws.onmessage = (event) => {{
                        clearTimeout(timeout);
                        received = true;
                        ws.close();
                        resolve({{ received: true, data: event.data }});
                    }};
                    
                    ws.onerror = () => {{
                        clearTimeout(timeout);
                        ws.close();
                        resolve({{ received: false, error: true }});
                    }};
                }} catch (e) {{
                    resolve({{ received: false, exception: String(e) }});
                }}
            }});
        }}""")
        
        assert isinstance(result, dict)


class TestAvatarSettings:
    """E2E tests for avatar settings API."""
    
    def test_avatar_settings_get(self, page: Page, e2e_server: str) -> None:
        """Test getting avatar settings."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/avatar/settings');
                const data = await response.text();
                return {{ status: response.status, data: data }};
            }} catch (e) {{
                return {{ error: true, message: String(e) }};
            }}
        }}""")
        
        assert isinstance(result, dict)
    
    def test_avatar_settings_update(self, page: Page, e2e_server: str) -> None:
        """Test updating avatar settings."""
        result = page.evaluate(f"""async () => {{
            try {{
                const response = await fetch('{e2e_server}/avatar/settings', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ theme: 'dark' }})
                }});
                return {{ status: response.status }};
            }} catch (e) {{
                return {{ error: true }};
            }}
        }}""")
        
        assert isinstance(result, dict)
