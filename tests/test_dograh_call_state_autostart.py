# MIT License
#
# Copyright (c) 2024 mhand

"""Tests for auto-starting the dograh call-state poller when a call begins.

Covers the SYNC -> async bridge added to ``DograhPollerRegistry``
(``request_start`` / ``request_stop``), the isolated run-id extraction
helper (``extract_run_id``), and the two long-lived call-initiation sites
that wire it (command_executor + advisor tool).

Everything is mocked: no network, no real event loops where avoidable.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.integrations.dograh_call_state import (
    DograhPollerRegistry,
    extract_run_id,
    get_poller_registry,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    get_poller_registry().clear()
    yield
    get_poller_registry().clear()


class TestExtractRunId:
    def test_workflow_run_id_key(self):
        assert extract_run_id({"workflow_run_id": 17}) == 17

    def test_run_id_key(self):
        assert extract_run_id({"run_id": 8}) == 8

    def test_top_level_id_key(self):
        assert extract_run_id({"id": 99}) == 99

    def test_nested_run_id(self):
        assert extract_run_id({"run": {"id": 42}}) == 42

    def test_precedence_workflow_run_id_first(self):
        assert extract_run_id({"workflow_run_id": 1, "id": 2}) == 1

    def test_missing_returns_none(self):
        assert extract_run_id({"unrelated": "x"}) is None

    def test_empty_returns_none(self):
        assert extract_run_id({}) is None

    def test_non_dict_returns_none(self):
        assert extract_run_id(None) is None  # type: ignore[arg-type]
        assert extract_run_id("nope") is None  # type: ignore[arg-type]

    def test_string_coercible_value(self):
        assert extract_run_id({"id": "55"}) == 55

    def test_non_coercible_value_falls_through(self):
        # A non-coercible top-level id falls through to the nested run.id.
        assert extract_run_id({"id": "abc", "run": {"id": 7}}) == 7


class _FakeLoop:
    """Minimal stand-in for an event loop; records scheduled coroutines."""

    def __init__(self):
        self.scheduled = []


class TestRequestStartStop:
    def test_request_start_schedules_on_registered_loop(self):
        reg = DograhPollerRegistry()
        start = MagicMock()
        stop = MagicMock()
        loop = _FakeLoop()
        reg.register(start=start, stop=stop, loop=loop)  # type: ignore[arg-type]

        captured = {}

        def fake_rct(coro, the_loop):
            captured["loop"] = the_loop
            captured["coro"] = coro
            coro.close()  # avoid "coroutine never awaited" warning
            return MagicMock()

        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe",
            side_effect=fake_rct,
        ) as rct:
            reg.request_start(5, 9)

        rct.assert_called_once()
        assert captured["loop"] is loop

    def test_request_start_noop_when_nothing_registered(self):
        reg = DograhPollerRegistry()
        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe"
        ) as rct:
            reg.request_start(1, 1)  # must not raise
        rct.assert_not_called()

    def test_request_start_noop_when_registered_without_loop(self):
        reg = DograhPollerRegistry()
        reg.register(start=MagicMock(), stop=MagicMock(), loop=None)
        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe"
        ) as rct:
            reg.request_start(1, 1)
        rct.assert_not_called()

    def test_request_stop_schedules_on_registered_loop(self):
        reg = DograhPollerRegistry()
        loop = _FakeLoop()
        reg.register(start=MagicMock(), stop=MagicMock(), loop=loop)  # type: ignore[arg-type]

        def fake_rct(coro, the_loop):
            coro.close()
            return MagicMock()

        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe",
            side_effect=fake_rct,
        ) as rct:
            reg.request_stop()
        rct.assert_called_once()

    def test_request_stop_noop_when_nothing_registered(self):
        reg = DograhPollerRegistry()
        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe"
        ) as rct:
            reg.request_stop()
        rct.assert_not_called()

    def test_request_start_never_raises_on_scheduling_error(self):
        reg = DograhPollerRegistry()
        reg.register(start=MagicMock(), stop=MagicMock(), loop=_FakeLoop())  # type: ignore[arg-type]
        with patch(
            "chatty_commander.integrations.dograh_call_state.asyncio.run_coroutine_threadsafe",
            side_effect=RuntimeError("loop closed"),
        ):
            reg.request_start(1, 1)  # swallowed, no raise


class TestCommandExecutorAutoStart:
    @pytest.fixture
    def executor(self):
        from chatty_commander.app.command_executor import CommandExecutor

        config = MagicMock()
        config.model_actions = {
            "call_support": {
                "action": "dograh_call",
                "workflow_id": 42,
                "phone_number": "+15555550100",
            },
        }
        return CommandExecutor(config, MagicMock(), MagicMock())

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_request_start_called_after_successful_call(
        self, mock_client_cls, executor
    ):
        instance = MagicMock()
        instance.initiate_call.return_value = {"workflow_run_id": 9}
        mock_client_cls.return_value.__enter__.return_value = instance

        reg = get_poller_registry()
        req_start = MagicMock()
        with patch.object(reg, "request_start", req_start):
            assert executor.execute_command("call_support") is True
        req_start.assert_called_once_with(42, 9)

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_request_start_not_called_when_no_run_id(
        self, mock_client_cls, executor
    ):
        instance = MagicMock()
        instance.initiate_call.return_value = {"unrelated": "x"}
        mock_client_cls.return_value.__enter__.return_value = instance

        reg = get_poller_registry()
        req_start = MagicMock()
        with patch.object(reg, "request_start", req_start):
            assert executor.execute_command("call_support") is True
        req_start.assert_not_called()

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_request_start_not_called_when_call_fails(
        self, mock_client_cls, executor
    ):
        from chatty_commander.integrations.dograh_client import DograhError

        instance = MagicMock()
        instance.initiate_call.side_effect = DograhError("boom")
        mock_client_cls.return_value.__enter__.return_value = instance

        reg = get_poller_registry()
        req_start = MagicMock()
        with patch.object(reg, "request_start", req_start):
            assert executor.execute_command("call_support") is False
        req_start.assert_not_called()


class TestAdvisorToolAutoStart:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_request_start_called_after_successful_call(self, mock_cls):
        from chatty_commander.advisors.tools.dograh_call import dograh_place_call_tool

        instance = MagicMock()
        instance.initiate_call.return_value = {"workflow_run_id": 17}
        mock_cls.return_value = instance

        reg = get_poller_registry()
        req_start = MagicMock()
        with patch.object(reg, "request_start", req_start):
            out = dograh_place_call_tool(42, "+15555550100")
        assert "17" in out
        req_start.assert_called_once_with(42, 17)

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_request_start_not_called_when_call_fails(self, mock_cls):
        from chatty_commander.advisors.tools.dograh_call import dograh_place_call_tool

        instance = MagicMock()
        instance.initiate_call.side_effect = RuntimeError("boom")
        mock_cls.return_value = instance

        reg = get_poller_registry()
        req_start = MagicMock()
        with patch.object(reg, "request_start", req_start):
            dograh_place_call_tool(42, "+15555550100")
        req_start.assert_not_called()


class TestWebModeRegistersLoop:
    """The FastAPI startup handler must register the running loop so that
    sync callers can schedule auto-start onto it."""

    @pytest.mark.asyncio
    async def test_startup_registers_running_loop(self):
        import asyncio

        from chatty_commander.app.config import Config
        from chatty_commander.web.web_mode import WebModeServer

        cfg = Config(config_file="")
        from chatty_commander.app.model_manager import ModelManager
        from chatty_commander.app.state_manager import StateManager

        sm = StateManager(cfg)
        mm = ModelManager(cfg)
        from chatty_commander.app.command_executor import CommandExecutor

        ce = CommandExecutor(cfg, mm, sm)
        server = WebModeServer(cfg, sm, mm, ce, no_auth=True)

        # Manually fire the registered startup handlers (TestClient would do
        # this, but we want the running-loop capture in an async context).
        for handler in server.app.router.on_startup:
            res = handler()
            if asyncio.iscoroutine(res):
                await res
        try:
            reg = get_poller_registry()
            assert reg.is_registered()
            # The captured loop is the one running this test.
            assert reg._loop is asyncio.get_running_loop()
        finally:
            for handler in server.app.router.on_shutdown:
                res = handler()
                if asyncio.iscoroutine(res):
                    await res
