from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_config_put_increments_metrics_and_applies():
    app = create_app(no_auth=True)
    client = TestClient(app)

    m1 = client.get("/api/v1/metrics").json()
    r = client.put("/api/v1/config", json={"foo": {"bar": 1}})
    assert r.status_code == 200
    m2 = client.get("/api/v1/metrics").json()
    assert m2["config_put"] >= m1.get("config_put", 0) + 1

    # Confirm config now exposes the key
    r = client.get("/api/v1/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "foo" in cfg and isinstance(cfg["foo"], dict)
