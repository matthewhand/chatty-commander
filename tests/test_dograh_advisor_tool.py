"""Tests for the dograh telephony advisor tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from chatty_commander.advisors.tools.dograh_call import dograh_place_call_tool
from chatty_commander.integrations.dograh_client import DograhUnavailableError


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
