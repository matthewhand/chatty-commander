"""Tests for chatty_commander.integrations.dograh_client.

The unit tests use respx to mock httpx — no network access. A separate
live smoke test is opt-in via DOGRAH_LIVE=1 and hits a real dograh stack
(see docker-compose.dograh.yml).
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx

from chatty_commander.integrations.dograh_client import (
    DograhClient,
    DograhConfig,
    DograhUnavailableError,
)


@pytest.fixture
def config() -> DograhConfig:
    return DograhConfig(base_url="http://dograh.test", api_key="dgr_test")


def test_config_from_env_requires_both_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
    monkeypatch.delenv("DOGRAH_API_KEY", raising=False)
    with pytest.raises(DograhUnavailableError):
        DograhConfig.from_env()


def test_config_from_env_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOGRAH_BASE_URL", "http://dograh.test/")
    monkeypatch.setenv("DOGRAH_API_KEY", "dgr_abc")
    cfg = DograhConfig.from_env()
    assert cfg.base_url == "http://dograh.test"
    assert cfg.api_key == "dgr_abc"


@respx.mock
def test_health_returns_payload(config: DograhConfig) -> None:
    route = respx.get("http://dograh.test/api/v1/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "version": "1.30.0"})
    )
    with DograhClient(config) as client:
        payload = client.health()
    assert route.called
    assert payload["status"] == "ok"


@respx.mock
def test_list_workflows_unwraps_items(config: DograhConfig) -> None:
    respx.get("http://dograh.test/api/v1/workflow/").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": 1, "name": "demo"}], "total": 1}
        )
    )
    with DograhClient(config) as client:
        wfs = client.list_workflows()
    assert wfs == [{"id": 1, "name": "demo"}]


@respx.mock
def test_list_workflows_passes_through_list(config: DograhConfig) -> None:
    respx.get("http://dograh.test/api/v1/workflow/").mock(
        return_value=httpx.Response(200, json=[{"id": 7}])
    )
    with DograhClient(config) as client:
        wfs = client.list_workflows()
    assert wfs == [{"id": 7}]


@respx.mock
def test_create_workflow_run_sends_context(config: DograhConfig) -> None:
    route = respx.post("http://dograh.test/api/v1/workflow/42/runs").mock(
        return_value=httpx.Response(201, json={"run_id": "abc"})
    )
    with DograhClient(config) as client:
        out = client.create_workflow_run(42, context={"phone": "+15555550100"})
    assert route.called
    assert route.calls.last.request.read() == b'{"context": {"phone": "+15555550100"}}'
    assert out["run_id"] == "abc"


@respx.mock
def test_bearer_header_is_set(config: DograhConfig) -> None:
    route = respx.get("http://dograh.test/api/v1/health").mock(
        return_value=httpx.Response(200, json={})
    )
    with DograhClient(config) as client:
        client.health()
    assert route.calls.last.request.headers["authorization"] == "Bearer dgr_test"


# ---------------------------------------------------------------------------
# Live smoke test — opt in by setting DOGRAH_LIVE=1 with a running stack.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    os.environ.get("DOGRAH_LIVE") != "1",
    reason="Set DOGRAH_LIVE=1 with a real dograh stack to run.",
)
def test_live_health() -> None:
    client = DograhClient()  # reads DOGRAH_BASE_URL / DOGRAH_API_KEY from env
    try:
        payload = client.health()
    finally:
        client.close()
    assert payload.get("status") == "ok"
    assert payload.get("deployment_mode") == "oss"
