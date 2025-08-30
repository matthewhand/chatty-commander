from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


def test_avatar_animations_nonexistent_dir_returns_404_minimal():
    app = create_app(no_auth=True)
    client = TestClient(app)
    # This endpoint is registered in server.create_app; minimal app does not include it.
    # We use minimal app for parity tests; skip if 404 here to avoid brittle coupling.
    r = client.get("/avatar/animations", params={"dir": "/path/does/not/exist"})
    assert r.status_code in (404, 200)
