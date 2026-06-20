"""Tests for chatty_commander.integrations.dograh_client.

The unit tests use respx to mock httpx — no network access. A separate
live smoke test is opt-in via DOGRAH_LIVE=1 and hits a real dograh stack
(see docker-compose.dograh.yml).
"""

from __future__ import annotations

import json
import os

import httpx
import pytest
import respx

from chatty_commander.integrations.dograh_client import (
    DograhClient,
    DograhConfig,
    DograhHTTPError,
    DograhUnavailableError,
    DograhValidationError,
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
    respx.get("http://dograh.test/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": 1, "name": "demo"}], "total": 1}
        )
    )
    with DograhClient(config) as client:
        wfs = client.list_workflows()
    assert wfs == [{"id": 1, "name": "demo"}]


@respx.mock
def test_list_workflows_passes_through_list(config: DograhConfig) -> None:
    respx.get("http://dograh.test/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(200, json=[{"id": 7}])
    )
    with DograhClient(config) as client:
        wfs = client.list_workflows()
    assert wfs == [{"id": 7}]


@respx.mock
def test_list_workflows_passes_status_filter(config: DograhConfig) -> None:
    route = respx.get("http://dograh.test/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(200, json=[])
    )
    with DograhClient(config) as client:
        client.list_workflows(status="active")
    assert route.calls.last.request.url.params["status"] == "active"


@respx.mock
def test_create_workflow_run_sends_mode_and_name(config: DograhConfig) -> None:
    route = respx.post("http://dograh.test/api/v1/workflow/42/runs").mock(
        return_value=httpx.Response(201, json={"id": 1, "workflow_id": 42})
    )
    with DograhClient(config) as client:
        out = client.create_workflow_run(42, mode="chat", name="smoke")
    assert route.called
    assert json.loads(route.calls.last.request.read()) == {
        "mode": "chat",
        "name": "smoke",
    }
    assert out["id"] == 1


@respx.mock
def test_initiate_call_minimal(config: DograhConfig) -> None:
    route = respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(200, json={"workflow_run_id": 9})
    )
    with DograhClient(config) as client:
        out = client.initiate_call(42)
    assert route.called
    assert json.loads(route.calls.last.request.read()) == {"workflow_id": 42}
    assert out["workflow_run_id"] == 9


@respx.mock
def test_initiate_call_with_phone_and_config(config: DograhConfig) -> None:
    route = respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(200, json={})
    )
    with DograhClient(config) as client:
        client.initiate_call(
            42, phone_number="+15555550100", telephony_configuration_id=7
        )
    assert json.loads(route.calls.last.request.read()) == {
        "workflow_id": 42,
        "phone_number": "+15555550100",
        "telephony_configuration_id": 7,
    }


@respx.mock
def test_initiate_call_rejects_invalid_phone_before_network(
    config: DograhConfig,
) -> None:
    """SECURITY: an invalid phone number is rejected before any HTTP request.

    Validation now lives in the client (not just the LLM tool), so BOTH the
    LLM-tool path and the config / wake-word path are covered. The respx route
    must NOT be called.
    """
    route = respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(200, json={})
    )
    with DograhClient(config) as client:
        for bad in ["not-a-number", "+1 555 0100", "12345", "", "+0123456789"]:
            with pytest.raises(DograhValidationError):
                client.initiate_call(42, phone_number=bad)
    assert not route.called


@respx.mock
def test_initiate_call_rejects_non_integer_workflow_id_before_network(
    config: DograhConfig,
) -> None:
    """A non-numeric workflow id is rejected before any HTTP request."""
    route = respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(200, json={})
    )
    with DograhClient(config) as client:
        with pytest.raises(DograhValidationError):
            client.initiate_call("not-an-int")  # type: ignore[arg-type]
    assert not route.called


@respx.mock
def test_initiate_call_coerces_numeric_string_workflow_id(
    config: DograhConfig,
) -> None:
    """A numeric-string workflow id is coerced to int and sent."""
    route = respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(200, json={"workflow_run_id": 1})
    )
    with DograhClient(config) as client:
        client.initiate_call("42")  # type: ignore[arg-type]
    assert json.loads(route.calls.last.request.read()) == {"workflow_id": 42}


@respx.mock
def test_get_workflow(config: DograhConfig) -> None:
    respx.get("http://dograh.test/api/v1/workflow/fetch/7").mock(
        return_value=httpx.Response(200, json={"id": 7, "name": "demo"})
    )
    with DograhClient(config) as client:
        wf = client.get_workflow(7)
    assert wf == {"id": 7, "name": "demo"}


@respx.mock
def test_list_workflow_runs_passes_pagination(config: DograhConfig) -> None:
    route = respx.get("http://dograh.test/api/v1/workflow/3/runs").mock(
        return_value=httpx.Response(
            200,
            json={"runs": [{"id": 1}], "total_count": 1, "page": 2, "limit": 5},
        )
    )
    with DograhClient(config) as client:
        payload = client.list_workflow_runs(3, page=2, limit=5)
    params = route.calls.last.request.url.params
    assert params["page"] == "2" and params["limit"] == "5"
    assert payload["runs"] == [{"id": 1}]


@respx.mock
def test_get_workflow_run(config: DograhConfig) -> None:
    respx.get("http://dograh.test/api/v1/workflow/3/runs/9").mock(
        return_value=httpx.Response(200, json={"id": 9, "is_completed": True})
    )
    with DograhClient(config) as client:
        run = client.get_workflow_run(3, 9)
    assert run["id"] == 9
    assert run["is_completed"] is True


@respx.mock
def test_http_error_extracts_dograh_detail(config: DograhConfig) -> None:
    respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(
            400, json={"detail": "telephony_not_configured"}
        )
    )
    with DograhClient(config) as client:
        with pytest.raises(DograhHTTPError) as exc_info:
            client.initiate_call(42, phone_number="+15555550100")
    err = exc_info.value
    assert err.status_code == 400
    assert err.detail == "telephony_not_configured"
    assert "telephony_not_configured" in str(err)
    assert err.method == "POST"
    # The URL must stay available as a structured attribute...
    assert err.url == "http://dograh.test/api/v1/telephony/initiate-call"
    # ...but must never appear in the client-visible message.
    assert "dograh.test" not in str(err)


def test_http_error_str_omits_url_but_repr_keeps_it() -> None:
    """str(e) is client-visible and must not leak the internal URL;
    repr(e) keeps everything for server-side logs."""
    err = DograhHTTPError(
        status_code=400,
        detail="telephony_not_configured",
        method="POST",
        url="http://internal.dograh:3010/api/v1/telephony/initiate-call",
    )
    msg = str(err)
    assert "http" not in msg
    assert "internal.dograh" not in msg
    assert "/api/v1" not in msg
    assert "400" in msg
    assert "telephony_not_configured" in msg
    # Structured attributes and repr retain the full request context.
    assert err.url == "http://internal.dograh:3010/api/v1/telephony/initiate-call"
    assert err.method == "POST"
    assert "internal.dograh" in repr(err)
    assert "POST" in repr(err)


@respx.mock
def test_http_error_handles_validation_list_detail(config: DograhConfig) -> None:
    """FastAPI returns ``detail`` as a list for 422 validation errors."""
    respx.post("http://dograh.test/api/v1/telephony/initiate-call").mock(
        return_value=httpx.Response(
            422,
            json={
                "detail": [
                    {"loc": ["body", "phone_number"], "msg": "field required"},
                ]
            },
        )
    )
    with DograhClient(config) as client:
        with pytest.raises(DograhHTTPError) as exc_info:
            client.initiate_call(42)
    assert exc_info.value.status_code == 422
    assert "field required" in exc_info.value.detail


@respx.mock
def test_http_error_falls_back_to_text(config: DograhConfig) -> None:
    """When the body isn't JSON, fall back to the raw text."""
    respx.get("http://dograh.test/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    with DograhClient(config) as client:
        with pytest.raises(DograhHTTPError) as exc_info:
            client.list_workflows()
    assert exc_info.value.status_code == 503
    assert "Service Unavailable" in exc_info.value.detail


@respx.mock
def test_x_api_key_header_is_set(config: DograhConfig) -> None:
    route = respx.get("http://dograh.test/api/v1/health").mock(
        return_value=httpx.Response(200, json={})
    )
    with DograhClient(config) as client:
        client.health()
    headers = route.calls.last.request.headers
    assert headers["x-api-key"] == "dgr_test"
    # Bearer auth must NOT be sent — dograh rejects it.
    assert "authorization" not in headers


# ---------------------------------------------------------------------------
# Live smoke test — opt in by setting DOGRAH_LIVE=1 with a running stack.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    os.environ.get("DOGRAH_LIVE") != "1",
    reason="Set DOGRAH_LIVE=1 with a real dograh stack to run.",
)
def test_live_health_and_auth() -> None:
    """Round-trip both unauthed (/health) and authed (/workflow/) endpoints.

    A failure on list_workflows specifically proves the X-API-Key header
    is reaching dograh correctly — /health alone is unauthed and would
    pass even if auth were broken.
    """
    client = DograhClient()  # reads DOGRAH_BASE_URL / DOGRAH_API_KEY from env
    try:
        payload = client.health()
        assert payload.get("status") == "ok"
        assert payload.get("deployment_mode") == "oss"

        # Authed call — must not 401.
        workflows = client.list_workflows()
        assert isinstance(workflows, list)
    finally:
        client.close()
