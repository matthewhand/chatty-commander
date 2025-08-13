from __future__ import annotations

import logging

from fastapi import FastAPI

from .auth import apply_cors, enable_no_auth_docs
from .lifecycle import register_lifecycle
from .routes.core import include_core_routes
from .routes.ws import include_ws_routes

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

    Additionally, attach extracted routers (core REST, websocket), CORS/docs toggles,
    and lifecycle hooks using dependency callables that bridge to the legacy server
    instance. This is behavior-preserving because routes and wiring rely on the same
    underlying state/config/executor.
    """
    legacy = _LegacyWebModeServer(
        config_manager=config_manager,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=bool(no_auth),
    )
    app = legacy.app

    # Docs visibility and CORS (behavior-preserving toggles)
    try:
        enable_no_auth_docs(app, no_auth=no_auth)
        apply_cors(app, no_auth=no_auth, origins=None)
        logger.debug("server.create_app: applied docs/cors policies (no_auth=%s)", no_auth)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to apply auth/cors policies; continuing with legacy defaults: %s", e)

    # Core REST routes
    try:
        core_router = include_core_routes(
            get_start_time=lambda: legacy.start_time,
            get_state_manager=lambda: legacy.state_manager,
            get_config_manager=lambda: legacy.config_manager,
            get_last_command=lambda: getattr(legacy, "last_command", None),
            get_last_state_change=lambda: legacy.last_state_change,
            execute_command_fn=lambda cmd: legacy.command_executor.execute_command(cmd),
        )
        app.include_router(core_router)
        logger.debug("server.create_app: included core REST routes from routes.core")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to include core routes, falling back to legacy-only: %s", e)

    # WebSocket route
    try:
        ws_router = include_ws_routes(
            get_connections=lambda: legacy.active_connections,
            set_connections=lambda s: setattr(legacy, "active_connections", s),
            get_state_snapshot=lambda: {
                "current_state": legacy.state_manager.current_state,
                "active_models": legacy.state_manager.get_active_models()
                if hasattr(legacy.state_manager, "get_active_models")
                else [],
                "timestamp": legacy.last_state_change.isoformat()
                if getattr(legacy, "last_state_change", None)
                else None,
            },
            on_message=None,  # preserve legacy: inbound messages are ignored today
            heartbeat_seconds=30.0,
        )
        app.include_router(ws_router)
        logger.debug("server.create_app: included websocket routes from routes.ws")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to include websocket routes; falling back to legacy-only: %s", e)

    # Avatar routes
    from .routes.avatar_api import router as avatar_api_router
    from .routes.avatar_ws import router as avatar_ws_router
    # Lifecycle hooks (no-op by default to preserve behavior)
    try:
        register_lifecycle(
            app,
            get_state_manager=lambda: legacy.state_manager,
            get_model_manager=lambda: legacy.model_manager,
            get_command_executor=lambda: legacy.command_executor,
            on_startup=None,
            on_shutdown=None,
        )
        logger.debug("server.create_app: registered lifecycle hooks")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to register lifecycle hooks; continuing: %s", e)

    # Avatar routes (with state management integration)
    try:
        app.include_router(avatar_ws_router)
        app.include_router(avatar_api_router)
        # Provide persona->theme resolution to WS manager from config
        try:
            from .routes import avatar_ws as _avatar_ws_mod
            def _resolve_theme(persona_id: str) -> str:
                cfg = getattr(legacy.config_manager, "config", {}) or {}
                gui = cfg.get("gui", {}) if isinstance(cfg, dict) else {}
                avatar = gui.get("avatar", {}) if isinstance(gui, dict) else {}
                mapping = avatar.get("persona_theme_map", {}) if isinstance(avatar, dict) else {}
                return mapping.get(persona_id, mapping.get("default", "default"))
            _avatar_ws_mod.manager.theme_resolver = _resolve_theme
            logger.debug("server.create_app: set WS theme_resolver from config")
        except Exception as e:
            logger.debug("server.create_app: theme_resolver not set: %s", e)
        logger.debug("server.create_app: included avatar ws/api routes")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to include avatar routes; continuing: %s", e)

    # Avatar settings routes
    try:
        from .routes.avatar_selector import router as avatar_selector_router
        from .routes.avatar_settings import include_avatar_settings_routes
        settings_router = include_avatar_settings_routes(get_config_manager=lambda: legacy.config_manager)
        app.include_router(settings_router)
        app.include_router(avatar_selector_router)
        logger.debug("server.create_app: included avatar settings + selector routes")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to include avatar settings/selector routes; continuing: %s", e)

    logger.debug("server.create_app constructed legacy WebModeServer and returned app")
    return app
