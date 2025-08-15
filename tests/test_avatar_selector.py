from chatty_commander.web.routes.avatar_selector import router as selector_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.avatar_selector import router as selector_router


def test_animation_selector_basic():
    app = FastAPI()
    app.include_router(selector_router)
    client = TestClient(app)

    resp = client.post("/avatar/animation/choose", json={"text": "Let's call a tool to compute"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] in ("hacking", "curious", "neutral")

    resp2 = client.post(
        "/avatar/animation/choose",
        json={"text": "Oops, an error occurred!", "candidate_labels": ["error", "success"]},
    )
    assert resp2.status_code == 200
    assert resp2.json()["label"] == "error"
