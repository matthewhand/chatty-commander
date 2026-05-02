# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import atexit
import logging
import signal
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def _handle_shutdown_signal(signum: int, frame: object) -> None:
    """Handle SIGTERM/SIGINT with structured logging."""
    sig_name = signal.Signals(signum).name
    timestamp = datetime.now(tz=UTC).isoformat()
    logger.info("Shutdown signal received (%s) at %s", sig_name, timestamp)
    logger.info("Shutting down gracefully...")
    # Re-raise the default handler so the process actually exits.
    signal.signal(signum, signal.SIG_DFL)
    signal.raise_signal(signum)


def _atexit_handler() -> None:
    """Log shutdown completion via atexit."""
    timestamp = datetime.now(tz=UTC).isoformat()
    logger.info("Shutdown complete at %s", timestamp)


def register_lifecycle(

    app: FastAPI,
    *,
    get_state_manager: Callable[[], Any],
    on_startup: Callable[[], None] | None = None,
    on_shutdown: Callable[[], None] | None = None,
) -> None:
    """
    Register minimal startup/shutdown hooks using provider callables.

    Notes:
    - Defaults are no-ops to preserve existing behavior.
    - We do not modify or duplicate any callbacks that legacy WebModeServer already registers.
    - This provides a stable boundary to extend later without impacting current tests.
    """

    @app.on_event("startup")
    async def _startup() -> None:  # noqa: D401
        # Register signal handlers for graceful shutdown logging.
        signal.signal(signal.SIGTERM, _handle_shutdown_signal)
        signal.signal(signal.SIGINT, _handle_shutdown_signal)
        atexit.register(_atexit_handler)

        # Logic flow
        # Intentionally minimal; invoke optional callback if present.
        if on_startup is not None:
            try:
                on_startup()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # noqa: D401
        # Process each item
        timestamp = datetime.now(tz=UTC).isoformat()
        logger.info("Shutting down gracefully... (%s)", timestamp)

        # Logic flow
        # Intentionally minimal; invoke optional callback if present.
        if on_shutdown is not None:
            try:
                on_shutdown()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass

        logger.info("Shutdown complete at %s", timestamp)
