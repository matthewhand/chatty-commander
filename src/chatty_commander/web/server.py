from __future__ import annotations

import logging

from fastapi import FastAPI

from .routes.core import include_core_routes

# For now we delegate to constructing the legacy WebModeServer to keep behavior stable.
from .web_mode import WebModeServer as _LegacyWebModeServer  # type: ignore

logger = logging.getLogger(__name__)


def create_app(
    config_manager=None,
    state_manager=None,
    model_manager=None,
    command_executor=None,
    no_auth: bool = False,
) -> FastAPI:
    """
    Create and return the FastAPI app.

    Current behavior: construct legacy WebModeServer and return its .app to ensure full
    backward compatibility. This establishes the stable assembly boundary for future
    extraction (routes/auth/lifecycle) without breaking tests.

    Additionally, attach extracted core REST routes using dependency callables that
    bridge to the legacy server instance. This is behavior-preserving because routes
    are equivalent and rely on the same underlying state/config/executor.
    """
    legacy = _LegacyWebModeServer(
        config_manager=config_manager,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=bool(no_auth),
    )
    app = legacy.app

    try:
        router = include_core_routes(
            get_start_time=lambda: legacy.start_time,
            get_state_manager=lambda: legacy.state_manager,
            get_config_manager=lambda: legacy.config_manager,
            get_last_command=lambda: getattr(legacy, "last_command", None),
            get_last_state_change=lambda: legacy.last_state_change,
            execute_command_fn=lambda cmd: legacy.command_executor.execute_command(cmd),
        )
        app.include_router(router)
        logger.debug("server.create_app: included core REST routes from routes.core")
    except Exception as e:  # noqa: BLE001
        # Defensive: if inclusion fails for any reason, keep legacy behavior intact
        logger.warning("Failed to include core routes, falling back to legacy-only: %s", e)

    logger.debug("server.create_app constructed legacy WebModeServer and returned app")
    return app
