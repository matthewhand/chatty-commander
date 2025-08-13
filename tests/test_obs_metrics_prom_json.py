from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_metrics_json_and_prom_exposed_and_populated():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Trigger a few requests
    client.get("/api/v1/health")
    client.get("/api/v1/config")

    rj = client.get("/metrics/json")
    assert rj.status_code == 200
    data = rj.json()
    assert "counters" in data and "histograms" in data and "gauges" in data

    rp = client.get("/metrics/prom")
    assert rp.status_code == 200
    text = rp.text
    assert "# TYPE http_requests_total counter" in text or "http_requests_total" in text
