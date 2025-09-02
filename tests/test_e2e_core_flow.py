# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


def test_e2e_core_health_status_config_state_metrics():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Health and status
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    r = client.get("/api/v1/status")
    assert r.status_code == 200

    # Metrics before
    m0 = client.get("/metrics/json")
    assert m0.status_code == 200
    data0 = m0.json()

    # Config PUT then GET
    r = client.put("/api/v1/config", json={"foo": {"bar": 1}})
    assert r.status_code == 200
    r = client.get("/api/v1/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "foo" in cfg and isinstance(cfg["foo"], dict)

    # Change state and verify
    r = client.post("/api/v1/state", json={"state": "computer"})
    assert r.status_code == 200
    r = client.get("/api/v1/state")
    assert r.status_code == 200
    assert r.json()["current_state"] == "computer"

    # Metrics after: ensure http_requests_total present and increased
    m1 = client.get("/metrics/json").json()
    counters = m1.get("counters", {})
    http_req = counters.get("http_requests_total", [])
    assert isinstance(http_req, list) and len(http_req) > 0
    # Find at least one sample for health route
    assert any(
        s["labels"].get("route") == "/api/v1/health"
        for s in http_req
        if isinstance(s, dict)
    )
