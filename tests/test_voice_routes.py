import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.command_executor import CommandExecutor


@pytest.fixture
def config():
    cfg = Config(config_file="")
    # Mock settings for the voice router to read
    cfg.config = {
        "wake_words": ["hey computer", "jarvis"],
        "voice": {"backend": "test_backend"}
    }
    return cfg


@pytest.fixture
def client(config):
    state_mgr = StateManager(config)
    model_mgr = ModelManager(config)
    executor = CommandExecutor(config, model_mgr, state_mgr)
    app = create_app(
        config_manager=config,
        state_manager=state_mgr,
        model_manager=model_mgr,
        command_executor=executor,
        no_auth=True,
    )
    return TestClient(app)


def test_voice_status(client):
    response = client.get("/api/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert data["running"] is False
    assert data["wake_words"] == ["hey computer", "jarvis"]
    assert data["backend"] == "test_backend"


def test_voice_start_and_stop(client):
    # Initially stopped
    status_resp = client.get("/api/voice/status")
    assert status_resp.json()["running"] is False

    # Start the voice pipeline
    start_resp = client.post("/api/voice/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "started"

    # Verify it is running
    status_resp = client.get("/api/voice/status")
    assert status_resp.json()["running"] is True

    # Starting again returns already_running
    start_resp_again = client.post("/api/voice/start")
    assert start_resp_again.status_code == 200
    assert start_resp_again.json()["status"] == "already_running"

    # Stop the voice pipeline
    stop_resp = client.post("/api/voice/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"

    # Verify it is stopped
    status_resp = client.get("/api/voice/status")
    assert status_resp.json()["running"] is False

    # Stopping again returns already_stopped
    stop_resp_again = client.post("/api/voice/stop")
    assert stop_resp_again.status_code == 200
    assert stop_resp_again.json()["status"] == "already_stopped"
