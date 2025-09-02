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

from chatty_commander.web.server import create_app


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
