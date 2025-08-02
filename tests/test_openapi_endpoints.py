import json
from fastapi.testclient import TestClient

from web_mode import app

client = TestClient(app)


def test_swagger_ui_docs_available():
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_openapi_json_available_and_has_paths():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    data = resp.json()
    assert isinstance(data, dict)
    assert "paths" in data and isinstance(data["paths"], dict)
