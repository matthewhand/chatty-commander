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

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.avatar_settings import include_avatar_settings_routes


class StubCfg:
    def __init__(self):
        self.config = {}
        self.saved = False

    def save_config(self, *_args, **_kwargs):
        self.saved = True


def test_avatar_settings_get_and_put():
    cfg = StubCfg()
    app = FastAPI()
    app.include_router(include_avatar_settings_routes(get_config_manager=lambda: cfg))
    client = TestClient(app)

    # GET defaults
    r = client.get("/avatar/config")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert "state_map" in data and "thinking" in data["state_map"]

    # PUT update
    payload = {"enabled": False, "state_map": {"thinking": "think2"}}
    r2 = client.put("/avatar/config", json=payload)
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2["enabled"] is False
    assert data2["state_map"]["thinking"] == "think2"
    assert cfg.saved is True
