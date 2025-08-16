from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_version_endpoint_ok():
    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("version") == "0.1.0"
    # git_sha may be None if git is unavailable in the environment
    assert "git_sha" in data
