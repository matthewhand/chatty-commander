from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_version_git_sha_is_string_or_null():
    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert "git_sha" in data
    assert (data["git_sha"] is None) or isinstance(data["git_sha"], str)
