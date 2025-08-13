from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_avatar_selector_labels():
    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.post("/avatar/animation/choose", json={"text": "calling tool now"})
    assert r.status_code == 200
    data = r.json()
    assert data["label"] in {
        "hacking",
        "neutral",
        "error",
        "warning",
        "success",
        "excited",
        "curious",
        "calm",
    }

    r2 = client.post(
        "/avatar/animation/choose",
        json={"text": "oops failure", "candidate_labels": ["error"]},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["label"] == "error"
