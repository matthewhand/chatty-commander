# MIT License
#
# Copyright (c) 2024 mhand
#
# Tests for src/chatty_commander/web/lifecycle.py

from __future__ import annotations

import signal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from chatty_commander.web import lifecycle

# ---------------------------------------------------------------------------
# Module-level handler functions
# ---------------------------------------------------------------------------


def test_handle_shutdown_signal_logs_and_reraises():
    """_handle_shutdown_signal logs structured info, restores default handler, re-raises."""
    with (
        patch.object(lifecycle.signal, "signal") as mock_signal,
        patch.object(lifecycle.signal, "raise_signal") as mock_raise,
        patch.object(lifecycle.logger, "info") as mock_info,
    ):
        lifecycle._handle_shutdown_signal(signal.SIGTERM, None)

    # Restores default handler for the received signal, then re-raises it.
    mock_signal.assert_called_once_with(signal.SIGTERM, signal.SIG_DFL)
    mock_raise.assert_called_once_with(signal.SIGTERM)

    # Two info log lines: signal-received and shutting-down.
    assert mock_info.call_count == 2
    first_call = mock_info.call_args_list[0]
    # The signal name 'SIGTERM' is one of the positional log args.
    assert "SIGTERM" in first_call.args


def test_handle_shutdown_signal_sigint():
    """SIGINT path resolves the signal name correctly."""
    with (
        patch.object(lifecycle.signal, "signal"),
        patch.object(lifecycle.signal, "raise_signal") as mock_raise,
        patch.object(lifecycle.logger, "info") as mock_info,
    ):
        lifecycle._handle_shutdown_signal(signal.SIGINT, None)

    mock_raise.assert_called_once_with(signal.SIGINT)
    assert "SIGINT" in mock_info.call_args_list[0].args


def test_atexit_handler_logs_completion():
    with patch.object(lifecycle.logger, "info") as mock_info:
        lifecycle._atexit_handler()
    assert mock_info.call_count == 1
    assert "Shutdown complete" in mock_info.call_args.args[0]


# ---------------------------------------------------------------------------
# register_lifecycle - registration wiring
# ---------------------------------------------------------------------------


def _find_handler(app: FastAPI, event_type: str):
    """Return the registered async handler for 'startup'/'shutdown'."""
    handlers = app.router.on_startup if event_type == "startup" else app.router.on_shutdown
    assert handlers, f"no {event_type} handlers registered"
    return handlers[-1]


def test_register_lifecycle_registers_both_events():
    app = FastAPI()
    before_startup = len(app.router.on_startup)
    before_shutdown = len(app.router.on_shutdown)

    lifecycle.register_lifecycle(app, get_state_manager=lambda: object())

    assert len(app.router.on_startup) == before_startup + 1
    assert len(app.router.on_shutdown) == before_shutdown + 1


# ---------------------------------------------------------------------------
# Startup handler behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_startup_registers_signals_and_atexit_no_callback():
    app = FastAPI()
    lifecycle.register_lifecycle(app, get_state_manager=lambda: object())
    startup = _find_handler(app, "startup")

    with (
        patch.object(lifecycle.signal, "signal") as mock_signal,
        patch.object(lifecycle.atexit, "register") as mock_atexit,
    ):
        await startup()

    # SIGTERM and SIGINT handlers installed.
    installed = {c.args[0] for c in mock_signal.call_args_list}
    assert signal.SIGTERM in installed
    assert signal.SIGINT in installed
    mock_atexit.assert_called_once_with(lifecycle._atexit_handler)


@pytest.mark.asyncio
async def test_startup_invokes_on_startup_callback():
    app = FastAPI()
    cb = MagicMock()
    lifecycle.register_lifecycle(
        app, get_state_manager=lambda: object(), on_startup=cb
    )
    startup = _find_handler(app, "startup")

    with (
        patch.object(lifecycle.signal, "signal"),
        patch.object(lifecycle.atexit, "register"),
    ):
        await startup()

    cb.assert_called_once_with()


@pytest.mark.asyncio
async def test_startup_swallows_on_startup_exception():
    app = FastAPI()
    cb = MagicMock(side_effect=RuntimeError("boom"))
    lifecycle.register_lifecycle(
        app, get_state_manager=lambda: object(), on_startup=cb
    )
    startup = _find_handler(app, "startup")

    with (
        patch.object(lifecycle.signal, "signal"),
        patch.object(lifecycle.atexit, "register"),
    ):
        # Must not raise despite the callback raising.
        await startup()

    cb.assert_called_once_with()


# ---------------------------------------------------------------------------
# Shutdown handler behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shutdown_logs_without_callback():
    app = FastAPI()
    lifecycle.register_lifecycle(app, get_state_manager=lambda: object())
    shutdown = _find_handler(app, "shutdown")

    with patch.object(lifecycle.logger, "info") as mock_info:
        await shutdown()

    messages = [c.args[0] for c in mock_info.call_args_list]
    assert any("Shutting down gracefully" in m for m in messages)
    assert any("Shutdown complete" in m for m in messages)


@pytest.mark.asyncio
async def test_shutdown_invokes_on_shutdown_callback():
    app = FastAPI()
    cb = MagicMock()
    lifecycle.register_lifecycle(
        app, get_state_manager=lambda: object(), on_shutdown=cb
    )
    shutdown = _find_handler(app, "shutdown")

    await shutdown()
    cb.assert_called_once_with()


@pytest.mark.asyncio
async def test_shutdown_swallows_on_shutdown_exception():
    app = FastAPI()
    cb = MagicMock(side_effect=ValueError("nope"))
    lifecycle.register_lifecycle(
        app, get_state_manager=lambda: object(), on_shutdown=cb
    )
    shutdown = _find_handler(app, "shutdown")

    with patch.object(lifecycle.logger, "info") as mock_info:
        # Must not raise despite callback raising.
        await shutdown()

    cb.assert_called_once_with()
    # Completion still logged after a swallowed callback error.
    messages = [c.args[0] for c in mock_info.call_args_list]
    assert any("Shutdown complete" in m for m in messages)


# ---------------------------------------------------------------------------
# End-to-end via TestClient lifespan (drives startup + shutdown together)
# ---------------------------------------------------------------------------


def test_lifespan_end_to_end_via_testclient():
    from fastapi.testclient import TestClient

    app = FastAPI()
    startup_cb = MagicMock()
    shutdown_cb = MagicMock()
    lifecycle.register_lifecycle(
        app,
        get_state_manager=lambda: object(),
        on_startup=startup_cb,
        on_shutdown=shutdown_cb,
    )

    with (
        patch.object(lifecycle.signal, "signal"),
        patch.object(lifecycle.atexit, "register"),
    ):
        with TestClient(app):
            # Inside the context, startup has fired.
            startup_cb.assert_called_once_with()
            shutdown_cb.assert_not_called()
        # On exit, shutdown has fired.
        shutdown_cb.assert_called_once_with()
