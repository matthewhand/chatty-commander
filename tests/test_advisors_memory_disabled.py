from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_advisors_memory_disabled_returns_400():
    app = create_app(no_auth=True)
    client = TestClient(app)
    r = client.get('/api/v1/advisors/memory', params={'platform': 'p', 'channel': 'c', 'user': 'u'})
    assert r.status_code == 400
    data = r.json()
    assert 'detail' in data
