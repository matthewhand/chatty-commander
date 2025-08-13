import json
from pathlib import Path

from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_avatar_animations_lists_allowed_files(tmp_path: Path):
    # Create temporary animation directory with a few files
    (tmp_path / "think.gif").write_bytes(b"gifdata")
    (tmp_path / "speak.mp4").write_bytes(b"mp4data")
    (tmp_path / "meta.json").write_text(json.dumps({"name": "meta"}))
    # Disallowed ext
    (tmp_path / "notes.txt").write_text("x")

    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.get("/avatar/animations", params={"dir": str(tmp_path)})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 3
    names = {a["name"] for a in data["animations"]}
    assert {"think", "speak", "meta"}.issubset(names)
