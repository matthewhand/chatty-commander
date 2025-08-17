from chatty_commander.app.config import Config
from chatty_commander.web.web_mode import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient


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
    assert resp.headers.get("access-control-allow-origin") in {"*", "http://example.com"}
    assert "access-control-allow-methods" in {k.lower() for k in resp.headers.keys()}


def test_cors_header_present_on_simple_get_when_no_auth():
    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.get("/api/v1/health", headers={"Origin": "http://example.com"})
    assert resp.status_code == 200
    # Response to a simple request should include ACAO when Origin is present
    assert resp.headers.get("access-control-allow-origin") in {"*", "http://example.com"}


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
