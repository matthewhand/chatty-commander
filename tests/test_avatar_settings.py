from chatty_commander.web.routes.avatar_settings import include_avatar_settings_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient


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
