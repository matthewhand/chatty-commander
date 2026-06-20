"""POST /api/restore (system.py) must honor the ALLOWED_PREF_KEYS allow-list.

A restore payload must not be able to overwrite arbitrary config keys (auth,
web_server, ...) — only allow-listed preference keys are applied.

Note: GET/PUT /api/preferences are owned by web/routes/preferences.py (which
registers first and wins dispatch); their allow-list is pinned in
``tests/test_preferences_routes.py``. system.py no longer registers those
duplicate handlers, so the only allow-list surface left here is /api/restore.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.system import ALLOWED_PREF_KEYS, include_system_routes


class FakeConfigManager:
    def __init__(self, config=None):
        self.config = config if config is not None else {}
        self.save_calls = 0

    def save_config(self):
        self.save_calls += 1


def _client(cfg_mgr):
    app = FastAPI()
    app.include_router(
        include_system_routes(
            get_start_time=lambda: 0.0,
            get_config_manager=lambda: cfg_mgr,
        )
    )
    return TestClient(app)


def test_restore_persists_allowed_key():
    cfg_mgr = FakeConfigManager()
    client = _client(cfg_mgr)
    resp = client.post("/api/restore", json={"data": {"ui": {"theme": "light"}}})
    assert resp.status_code == 200
    assert cfg_mgr.config["ui"] == {"theme": "light"}
    assert "ui" in ALLOWED_PREF_KEYS


def test_restore_rejects_disallowed_key():
    cfg_mgr = FakeConfigManager({"auth": {"api_key": "secret"}})
    client = _client(cfg_mgr)
    resp = client.post(
        "/api/restore",
        json={"data": {"general": {"x": 1}, "auth": {"api_key": "attacker"}}},
    )
    assert resp.status_code == 200
    assert cfg_mgr.config["general"] == {"x": 1}
    # auth must remain untouched by a restore payload.
    assert cfg_mgr.config["auth"] == {"api_key": "secret"}
