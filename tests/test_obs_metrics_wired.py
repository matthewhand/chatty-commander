"""Tests verifying that obs/metrics middleware and router are wired into the FastAPI app."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def _make_app():
    """Create a minimal WebModeServer app for testing."""
    from chatty_commander.web.web_mode import WebModeServer

    config = MagicMock()
    config.web_server = {}
    config.advisors = {}
    config.default_state = "idle"
    config.state_models = {}
    config.api_endpoints = {}
    config.commands = {}
    config.llm_manager = None
    config.voice_pipeline = None

    state_manager = MagicMock()
    state_manager.current_state = "idle"
    state_manager.add_state_change_callback = MagicMock()

    model_manager = MagicMock()
    command_executor = MagicMock()

    server = WebModeServer(
        config_manager=config,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=True,
    )
    return server.app


def test_metrics_json_endpoint_registered():
    """GET /metrics/json should be registered and return a dict."""
    from fastapi.testclient import TestClient

    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/metrics/json")
    assert response.status_code == 200
    data = response.json()
    # Should have the standard registry keys
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data


def test_metrics_prom_endpoint_registered():
    """GET /metrics/prom should be registered and return Prometheus text format."""
    from fastapi.testclient import TestClient

    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/metrics/prom")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_request_metrics_middleware_tracks_requests():
    """After making a request, http_requests_total counter should be non-zero."""
    from fastapi.testclient import TestClient
    from chatty_commander.obs.metrics import DEFAULT_REGISTRY

    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)

    # Make a request to populate the counter
    client.get("/health")

    # Check the metrics endpoint reflects the request
    response = client.get("/metrics/json")
    assert response.status_code == 200
    data = response.json()
    counters = data.get("counters", {})
    # http_requests_total should exist and have at least one sample
    assert "http_requests_total" in counters
    samples = counters["http_requests_total"]
    total = sum(s.get("value", 0) for s in samples)
    assert total > 0, "Expected at least one request to be counted"
