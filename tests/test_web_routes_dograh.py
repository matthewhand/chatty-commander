"""Tests for /api/v1/dograh/* web routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.integrations.dograh_client import (
    DograhHTTPError,
    DograhUnavailableError,
)
from chatty_commander.web.routes.dograh import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestDograhStatusEndpoint:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_status_available_when_reachable(self, mock_cls):
        instance = MagicMock()
        instance.health.return_value = {"status": "ok", "version": "1.30.0"}
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/status")
        assert r.status_code == 200
        body = r.json()
        assert body["available"] is True
        assert body["health"]["version"] == "1.30.0"
        assert body["health"]["status"] == "ok"
        assert body["reason"] is None

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_status_projects_health_allowlist(self, mock_cls):
        # Unexpected keys in dograh's /health body must NOT reach the client.
        instance = MagicMock()
        instance.health.return_value = {
            "status": "ok",
            "version": "1.30.0",
            "internal_hostname": "dograh-api.internal.svc",
            "db_dsn": "postgres://user:pass@db:5432/dograh",
            "secrets": {"api_key": "dgr_supersecret"},
        }
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/status")
        assert r.status_code == 200
        body = r.json()
        assert body["available"] is True
        assert set(body["health"].keys()) == {"status", "version"}
        assert "internal_hostname" not in body["health"]
        assert "db_dsn" not in body["health"]
        assert "secrets" not in body["health"]
        # And no leaked value appears anywhere in the serialized response.
        assert "internal" not in r.text
        assert "postgres" not in r.text
        assert "dgr_supersecret" not in r.text

    @patch(
        "chatty_commander.integrations.dograh_client.DograhConfig.from_env",
        side_effect=DograhUnavailableError("DOGRAH_BASE_URL not set"),
    )
    def test_status_unavailable_when_unconfigured(self, _mock, monkeypatch):
        monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
        monkeypatch.delenv("DOGRAH_API_KEY", raising=False)

        r = _client().get("/api/v1/dograh/status")
        assert r.status_code == 200
        body = r.json()
        assert body["available"] is False
        assert "DOGRAH_BASE_URL" in body["reason"]
        assert body["health"] is None

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_status_unavailable_when_unreachable(self, mock_cls):
        instance = MagicMock()
        instance.health.side_effect = ConnectionError("nope")
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/status")
        body = r.json()
        assert body["available"] is False
        # Reason must be a generic constant — not the exception text.
        assert body["reason"] == "unreachable"

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_status_unreachable_does_not_leak_url(self, mock_cls):
        # When the client raises a DograhHTTPError carrying the internal URL,
        # the route must NOT surface the hostname to the caller.
        instance = MagicMock()
        instance.health.side_effect = DograhHTTPError(
            status_code=503,
            detail="service unavailable",
            method="GET",
            url="http://dograh-api.internal.svc:8000/api/v1/health",
        )
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/status")
        body = r.json()
        assert body["available"] is False
        assert body["reason"] == "unreachable"
        # No URL, hostname, or HTTP detail anywhere in the response body.
        assert "dograh-api.internal.svc" not in r.text
        assert "http://" not in r.text
        assert "8000" not in r.text
        assert "service unavailable" not in r.text


class TestDograhWorkflowsEndpoint:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_workflows_returned(self, mock_cls):
        instance = MagicMock()
        instance.list_workflows.return_value = [
            {"id": 1, "name": "demo", "status": "active"},
            {"id": 2, "name": "other", "status": "archived"},
        ]
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/workflows")
        assert r.status_code == 200
        assert r.json() == [
            {"id": 1, "name": "demo", "status": "active"},
            {"id": 2, "name": "other", "status": "archived"},
        ]

    @patch(
        "chatty_commander.integrations.dograh_client.DograhConfig.from_env",
        side_effect=DograhUnavailableError("env missing"),
    )
    def test_workflows_empty_when_unconfigured(self, _mock, monkeypatch):
        monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
        monkeypatch.delenv("DOGRAH_API_KEY", raising=False)

        r = _client().get("/api/v1/dograh/workflows")
        assert r.status_code == 200
        assert r.json() == []

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_workflows_empty_on_http_error(self, mock_cls):
        instance = MagicMock()
        instance.list_workflows.side_effect = DograhHTTPError(
            status_code=500, detail="oops", method="GET", url="http://x/workflow/fetch"
        )
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/workflows")
        assert r.status_code == 200
        assert r.json() == []

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_workflows_skip_records_without_id(self, mock_cls):
        instance = MagicMock()
        instance.list_workflows.return_value = [
            {"id": 1, "name": "ok"},
            {"name": "malformed"},  # missing id
        ]
        mock_cls.return_value = instance

        r = _client().get("/api/v1/dograh/workflows")
        assert [wf["id"] for wf in r.json()] == [1]
