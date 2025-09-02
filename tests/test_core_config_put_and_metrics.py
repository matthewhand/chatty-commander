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
