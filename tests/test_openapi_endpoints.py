import json
from fastapi.testclient import TestClient

from web_mode import app

client = TestClient(app)

def test_swagger_ui_docs_available():\n    resp = client.get('/docs')\n    assert resp.status_code == 200\n    assert 'text/html' in resp.headers.get('content-type','')\n

def test_openapi_json_available_and_has_paths():\n    resp = client.get('/openapi.json')\n    assert resp.status_code == 200\n    assert 'application/json' in resp.headers.get('content-type','')\n    data = resp.json()\n    assert isinstance(data, dict)\n    assert 'paths' in data and isinstance(data['paths'], dict)\n
