from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI


def register_lifecycle(
    app: FastAPI,
    *,
    get_state_manager: Callable[[], Any],
    get_model_manager: Callable[[], Any],
    get_command_executor: Callable[[], Any],
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
        # Intentionally minimal; invoke optional callback if present.
        if on_startup is not None:
            try:
                on_startup()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # noqa: D401
        # Intentionally minimal; invoke optional callback if present.
        if on_shutdown is not None:
            try:
                on_shutdown()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass
