"""The RateLimitMiddleware default must be sane and config-overridable.

Previously it was wired with requests_per_minute=10000, which effectively
disabled the limiter. It now defaults to 600/min and reads
web_server.rate_limit_rpm from config when present.
"""

from __future__ import annotations

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import RateLimitMiddleware, WebModeServer


def _build_server(rate_limit_rpm=None) -> WebModeServer:
    config = Config()
    if rate_limit_rpm is not None:
        config.web_server["rate_limit_rpm"] = rate_limit_rpm
    state_manager = StateManager(config)
    model_manager = ModelManager(config)
    command_executor = CommandExecutor(config, model_manager, state_manager)
    return WebModeServer(
        config, state_manager, model_manager, command_executor, no_auth=True
    )


def _rate_limit_rpm(app) -> int:
    mw = next(m for m in app.user_middleware if m.cls is RateLimitMiddleware)
    return mw.kwargs["requests_per_minute"]


def test_default_rate_limit_is_sane():
    server = _build_server()
    rpm = _rate_limit_rpm(server.app)
    assert rpm == 600
    # Sanity: nowhere near the old effectively-off value.
    assert rpm < 10000


def test_rate_limit_is_configurable():
    server = _build_server(rate_limit_rpm=120)
    assert _rate_limit_rpm(server.app) == 120


def test_invalid_rate_limit_falls_back_to_default():
    server = _build_server(rate_limit_rpm="not-a-number")
    assert _rate_limit_rpm(server.app) == 600


def test_nonpositive_rate_limit_falls_back_to_default():
    server = _build_server(rate_limit_rpm=0)
    assert _rate_limit_rpm(server.app) == 600
