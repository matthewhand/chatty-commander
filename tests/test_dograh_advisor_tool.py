"""Tests for the dograh telephony advisor tool."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.advisors.tools.dograh_call import dograh_place_call_tool
from chatty_commander.integrations.dograh_client import (
    DograhHTTPError,
    DograhUnavailableError,
)


@patch("chatty_commander.integrations.dograh_client.DograhClient")
def test_place_call_success_returns_run_id(mock_cls):
    instance = MagicMock()
    instance.initiate_call.return_value = {"workflow_run_id": 17}
    mock_cls.return_value = instance

    result = dograh_place_call_tool(42, "+15555550100")

    assert "workflow_run_id=17" in result
    instance.initiate_call.assert_called_once_with(42, phone_number="+15555550100")
    instance.close.assert_called_once()


@patch("chatty_commander.integrations.dograh_client.DograhClient")
def test_place_call_falls_back_to_top_level_id(mock_cls):
    instance = MagicMock()
    instance.initiate_call.return_value = {"id": 99}
    mock_cls.return_value = instance

    result = dograh_place_call_tool(7, "+15551112222")

    assert "workflow_run_id=99" in result


@patch(
    "chatty_commander.integrations.dograh_client.DograhConfig.from_env",
    side_effect=DograhUnavailableError("env missing"),
)
def test_place_call_unconfigured_returns_status_string(_mock, monkeypatch):
    monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
    monkeypatch.delenv("DOGRAH_API_KEY", raising=False)

    result = dograh_place_call_tool(42, "+15555550100")

    assert "dograh not configured" in result
    assert "env missing" in result


@patch("chatty_commander.integrations.dograh_client.DograhClient")
def test_place_call_request_error_returns_status_string(mock_cls):
    instance = MagicMock()
    instance.initiate_call.side_effect = RuntimeError("boom")
    mock_cls.return_value = instance

    result = dograh_place_call_tool(42, "+15555550100")

    assert "dograh call failed" in result
    assert "boom" in result
    instance.close.assert_called_once()


@patch("chatty_commander.integrations.dograh_client.DograhClient")
def test_place_call_http_error_logs_status_detail_not_url(mock_cls, caplog):
    """The warning log must carry status/detail but never the internal
    request URL, which could leak into surfaced logs."""
    instance = MagicMock()
    instance.initiate_call.side_effect = DograhHTTPError(
        status_code=400,
        detail="telephony_not_configured",
        method="POST",
        url="http://internal.dograh:3010/api/v1/telephony/initiate-call",
    )
    mock_cls.return_value = instance

    with caplog.at_level(
        "WARNING", logger="chatty_commander.advisors.tools.dograh_call"
    ):
        result = dograh_place_call_tool(42, "+15555550100")

    assert "dograh call failed" in result
    assert "telephony_not_configured" in result
    assert "internal.dograh" not in result

    warning_text = "\n".join(
        rec.getMessage() for rec in caplog.records if rec.levelname == "WARNING"
    )
    assert "status=400" in warning_text
    assert "telephony_not_configured" in warning_text
    assert "internal.dograh" not in warning_text
    assert "http" not in warning_text
    instance.close.assert_called_once()


# ---------------------------------------------------------------------------
# Regression tests for the provider-import bug.
#
# advisors/providers.py used to import "..tools.X" which resolves to
# chatty_commander.tools.X — the wrong package (chatty_commander has both
# tools/ and advisors/tools/). The except-ImportError swallowed the failure
# so the FunctionTool was silently never registered with the LLM agent.
# These tests pin the correct import path AND verify the tool ends up
# in the agent's tools list when enabled.
# ---------------------------------------------------------------------------
def test_provider_import_path_resolves_to_advisors_tools():
    """The dotted path used by providers.py must resolve to a real module
    that exports dograh_call_tool_instance."""
    module = importlib.import_module(
        "chatty_commander.advisors.tools.dograh_call"
    )
    assert hasattr(module, "dograh_call_tool_instance")


@pytest.fixture(autouse=True)
def _stub_agents_module(monkeypatch):
    """providers.py needs the openai-agents SDK to construct an Agent.
    Stub the minimum surface so AgentsProvider.__init__ runs in tests
    without requiring the real SDK."""
    import sys
    import types

    fake_agents = types.ModuleType("agents")

    class _StubAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def chat(self, prompt):
            return ""

    fake_agents.Agent = _StubAgent
    fake_agents.FunctionTool = type(
        "FunctionTool",
        (),
        {"__init__": lambda self, **kw: setattr(self, "kwargs", kw)},
    )

    monkeypatch.setitem(sys.modules, "agents", fake_agents)

    # Re-import providers so it sees the fake agents module + the real
    # tool modules with FunctionTool re-stamped.
    import chatty_commander.advisors.providers as providers_mod

    importlib.reload(providers_mod)
    import chatty_commander.advisors.tools.browser_analyst as ba

    importlib.reload(ba)
    import chatty_commander.advisors.tools.dograh_call as dc

    importlib.reload(dc)
    yield


def test_agents_provider_loads_dograh_call_when_enabled():
    """When the advisors config opts in to dograh_call, the tool must
    actually end up in the constructed Agent's tools list."""
    from chatty_commander.advisors.providers import CompletionProvider

    provider = CompletionProvider(
        {
            "api_key": "k",
            "model": "test",
            "base_url": "http://example",
            "tools": {
                "browser_analyst": {"enabled": False},
                "dograh_call": {"enabled": True},
            },
        }
    )
    tool_names = [
        getattr(t, "kwargs", {}).get("name") for t in provider.agent.kwargs["tools"]
    ]
    assert "dograh_place_call" in tool_names


def test_agents_provider_omits_dograh_call_when_not_enabled():
    from chatty_commander.advisors.providers import CompletionProvider

    provider = CompletionProvider(
        {
            "api_key": "k",
            "model": "test",
            "base_url": "http://example",
            "tools": {"browser_analyst": {"enabled": False}},
        }
    )
    tool_names = [
        getattr(t, "kwargs", {}).get("name") for t in provider.agent.kwargs["tools"]
    ]
    assert "dograh_place_call" not in tool_names
