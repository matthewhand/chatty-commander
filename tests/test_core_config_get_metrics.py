from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_config_get_increments_metrics():
    app = create_app(no_auth=True)
    client = TestClient(app)

    m1 = client.get("/api/v1/metrics").json()
    client.get("/api/v1/config")
    m2 = client.get("/api/v1/metrics").json()

    assert m2["config_get"] >= m1.get("config_get", 0) + 1
