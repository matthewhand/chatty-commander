import json
from pathlib import Path

from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer
from fastapi.testclient import TestClient


class DummyConfig:
    def __init__(self) -> None:
        # Minimal paths and actions for ModelManager/Executor
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


def test_avatar_animations_lists_allowed_files(tmp_path: Path):
    # Create temporary animation directory with a few files
    (tmp_path / "think.gif").write_bytes(b"gifdata")
    (tmp_path / "speak.mp4").write_bytes(b"mp4data")
    (tmp_path / "meta.json").write_text(json.dumps({"name": "meta"}))
    # Disallowed ext
    (tmp_path / "notes.txt").write_text("x")

    cfg = DummyConfig()
    sm = StateManager()
    mm = ModelManager(cfg)
    ce = CommandExecutor(cfg, mm, sm)
    server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
    client = TestClient(server.app)

    r = client.get("/avatar/animations", params={"dir": str(tmp_path)})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 3
    names = {a["name"] for a in data["animations"]}
    assert {"think", "speak", "meta"}.issubset(names)
