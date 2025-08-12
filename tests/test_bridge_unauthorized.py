from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_bridge_unauthorized_without_token():
    app = create_app(no_auth=True)
    client = TestClient(app)
    r = client.post(
        '/bridge/event', json={'platform': 'x', 'channel': 'y', 'user': 'u', 'text': 'hi'}
    )
    assert r.status_code == 401
