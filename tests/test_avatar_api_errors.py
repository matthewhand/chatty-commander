from fastapi.testclient import TestClient

from chatty_commander.web.server import create_app


def test_avatar_animations_nonexistent_dir_returns_404():
    app = create_app(no_auth=True)
    client = TestClient(app)
    r = client.get("/avatar/animations", params={"dir": "/path/does/not/exist"})
    assert r.status_code == 404
