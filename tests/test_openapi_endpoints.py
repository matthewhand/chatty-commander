from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager

# Import FastAPI app from the source package
from chatty_commander.web.web_mode import WebModeServer
from fastapi.testclient import TestClient

# Minimal app factory matching current constructor signatures
_config = Config()
_state = StateManager()
_models = ModelManager(_config)
_executor = CommandExecutor(_config, _models, _state)
_server = WebModeServer(config_manager=_config, state_manager=_state, model_manager=_models, command_executor=_executor, no_auth=True)
app = _server.app

client = TestClient(app)


def test_swagger_ui_docs_available():
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_openapi_json_available_and_has_paths():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    data = resp.json()
    assert isinstance(data, dict)
    assert "paths" in data and isinstance(data["paths"], dict)
