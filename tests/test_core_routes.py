"""Consolidated tests for core API v1 routes and health/db checks."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.core import include_core_routes
from chatty_commander.web.web_mode import create_app


@pytest.fixture()
def client():
    """Shared test client using a no-auth app instance."""
    app = create_app(no_auth=True)
    return TestClient(app)


# -- config ------------------------------------------------------------------


def test_config_get_increments_metrics(client):
    m1 = client.get("/api/v1/metrics").json()
    client.get("/api/v1/config")
    m2 = client.get("/api/v1/metrics").json()

    assert m2["config_get"] >= m1.get("config_get", 0) + 1


def test_config_put_increments_metrics_and_applies(client):
    m1 = client.get("/api/v1/metrics").json()
    r = client.put("/api/v1/config", json={"foo": {"bar": 1}})
    assert r.status_code == 200
    m2 = client.get("/api/v1/metrics").json()
    assert m2["config_put"] >= m1.get("config_put", 0) + 1

    # Confirm config now exposes the key
    r = client.get("/api/v1/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "foo" in cfg and isinstance(cfg["foo"], dict)


# -- command -----------------------------------------------------------------


def test_command_unknown_returns_200_minimal_app(client):
    resp = client.post("/api/v1/command", json={"command": "does_not_exist"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert isinstance(data["message"], str)
    assert (
        "not found" in data["message"].lower()
        or "no configuration" in data["message"].lower()
    )
    assert data["execution_time"] > 0


def test_metrics_increment_on_unknown_command(client):
    m1 = client.get("/api/v1/metrics").json()
    resp = client.post("/api/v1/command", json={"command": "unknown_command"})
    assert resp.status_code in (200, 404)
    m2 = client.get("/api/v1/metrics").json()

    assert m2["command_post"] >= m1.get("command_post", 0) + 1


# -- state -------------------------------------------------------------------


def test_state_change_invalid_value_returns_422(client):
    r = client.post("/api/v1/state", json={"state": "invalid"})
    assert r.status_code == 422


# -- health / database (from test_core_health_db) -------------------------


def _health_app(config_dict):
    """Build a minimal FastAPI app with core routes for health testing."""
    config_mock = MagicMock()
    config_mock.config = config_dict

    router = include_core_routes(
        get_start_time=lambda: 0,
        get_state_manager=MagicMock(),
        get_config_manager=lambda: config_mock,
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=lambda x: True,
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_db_not_configured():
    c = _health_app({})
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "not_configured"


def test_health_db_healthy():
    c = _health_app({"database_url": "sqlite:///:memory:"})
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "healthy"


def test_health_db_unreachable():
    c = _health_app(
        {
            "database_url": "postgresql://invalid_user:invalid_pass@localhost:1/invalid_db"
        }
    )
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "unreachable"
