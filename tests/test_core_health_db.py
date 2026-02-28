from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from chatty_commander.web.routes.core import include_core_routes

def test_health_db_not_configured():
    config_mock = MagicMock()
    config_mock.config = {}

    router = include_core_routes(
        get_start_time=lambda: 0,
        get_state_manager=MagicMock(),
        get_config_manager=lambda: config_mock,
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=lambda x: True
    )

    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "not_configured"

def test_health_db_healthy():
    config_mock = MagicMock()
    config_mock.config = {"database_url": "sqlite:///:memory:"}

    router = include_core_routes(
        get_start_time=lambda: 0,
        get_state_manager=MagicMock(),
        get_config_manager=lambda: config_mock,
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=lambda x: True
    )

    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "healthy"

def test_health_db_unreachable():
    config_mock = MagicMock()
    # A malformed database URL or an unreachable port
    config_mock.config = {"database_url": "postgresql://invalid_user:invalid_pass@localhost:1/invalid_db"}

    router = include_core_routes(
        get_start_time=lambda: 0,
        get_state_manager=MagicMock(),
        get_config_manager=lambda: config_mock,
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=lambda x: True
    )

    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "unreachable"
