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

from fastapi.testclient import TestClient

from chatty_commander.app.config import Config
from chatty_commander.web.web_mode import create_app


def test_cors_allows_any_origin_in_no_auth_mode():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Simulate a browser preflight for a typical JSON POST
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    resp = client.options("/api/v1/health", headers=headers)
    assert resp.status_code in (200, 204)
    # In FastAPI/Starlette, allow all origins is reflected as '*' when no allow_credentials
    assert resp.headers.get("access-control-allow-origin") in {
        "*",
        "http://example.com",
    }
    assert "access-control-allow-methods" in {k.lower() for k in resp.headers.keys()}


def test_cors_header_present_on_simple_get_when_no_auth():
    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.get("/api/v1/health", headers={"Origin": "http://example.com"})
    assert resp.status_code == 200
    # Response to a simple request should include ACAO when Origin is present
    assert resp.headers.get("access-control-allow-origin") in {
        "*",
        "http://example.com",
    }


def test_cors_respects_configured_origins():
    """Custom origins can be supplied via Config for test parity with production."""

    cfg = Config()
    cfg.config.setdefault("web", {})["allowed_origins"] = [
        "http://foo.example",
        "http://bar.example",
    ]
    app = create_app(no_auth=False, config=cfg)
    client = TestClient(app)

    headers = {
        "Origin": "http://bar.example",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    resp = client.options("/api/v1/health", headers=headers)
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://bar.example"
