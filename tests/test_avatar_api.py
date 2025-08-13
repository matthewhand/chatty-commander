from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.chatty_commander.web.routes.avatar_api import router as avatar_router


def test_list_animations_endpoint(tmp_path: Path):
    # Create a fake animations directory structure
    anim_dir = tmp_path / "anims"
    anim_dir.mkdir()
    # some allowed and disallowed files
    allowed = ["think_idle.webm", "hack_loop.mp4", "speak.gif", "error.png"]
    for name in allowed:
        (anim_dir / name).write_bytes(b"x")
    (anim_dir / "notes.txt").write_text("ignore")

    app = FastAPI()
    app.include_router(avatar_router)
    client = TestClient(app)
    resp = client.get("/avatar/animations", params={"dir": str(anim_dir)})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["count"] == 4
    files = {a["file"] for a in data["animations"]}
    assert files == set(allowed)
    # category hints should map at least some
    categories = {a["name"]: a["category"] for a in data["animations"]}
    assert categories["think_idle"] in ("thinking", "idle")
    assert categories["hack_loop"] in ("tool_calling", "processing")
