"""Tests for startup env-var validation (ROADMAP "Secrets validation at startup").

Required vars are enforced only for explicitly enabled features; a default
config with zero environment variables must always boot. Failures aggregate
every missing var into one clear message.
"""

import logging
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.env_validation import (
    EnvValidationError,
    collect_env_report,
    validate_startup_env,
)

# ── helpers ──────────────────────────────────────────────────────────────


def _cfg(advisors=None, model_actions=None):
    return SimpleNamespace(
        advisors=advisors if advisors is not None else {"enabled": False},
        model_actions=model_actions if model_actions is not None else {},
    )


DOGRAH_ACTIONS = {
    "call_support": {"action": "dograh_call", "workflow_id": 1},
    "ring_home": {"action": "dograh_call", "workflow_id": 2},
    "screenshot": {"action": "keypress", "keys": "take_screenshot"},
}


# ── zero-config / disabled features need nothing ─────────────────────────


def test_default_config_boots_with_zero_env():
    """The stock Config with no env vars set must produce no errors/warnings."""
    config = Config(config_file="")
    report = collect_env_report(config, env={})
    assert report.ok
    assert report.warnings == []


def test_disabled_features_require_nothing():
    report = collect_env_report(_cfg(), env={})
    assert report.ok
    assert report.warnings == []
    # validate_startup_env must not raise either
    validate_startup_env(_cfg(), env={})


def test_mock_or_malformed_config_treated_as_disabled():
    # Tests elsewhere patch Config with MagicMocks; validation must not
    # misread mock attributes as enabled features (or crash on them).
    assert collect_env_report(MagicMock(), env={}).ok
    assert collect_env_report(SimpleNamespace(), env={}).ok
    assert collect_env_report(
        _cfg(advisors="bogus", model_actions=["not", "a", "dict"]), env={}
    ).ok


# ── advisors ─────────────────────────────────────────────────────────────


def test_advisors_enabled_without_key_fails_fast():
    config = _cfg(advisors={"enabled": True})
    report = collect_env_report(config, env={})
    assert [i.var for i in report.missing] == ["OPENAI_API_KEY"]
    with pytest.raises(EnvValidationError) as exc_info:
        validate_startup_env(config, env={})
    assert "OPENAI_API_KEY" in str(exc_info.value)
    assert exc_info.value.missing_vars == ["OPENAI_API_KEY"]


def test_advisors_enabled_with_env_key_ok():
    config = _cfg(advisors={"enabled": True})
    report = validate_startup_env(config, env={"OPENAI_API_KEY": "sk-test"})
    assert report.ok


def test_advisors_enabled_with_config_key_ok():
    config = _cfg(
        advisors={"enabled": True, "providers": {"api_key": "sk-from-config"}}
    )
    assert collect_env_report(config, env={}).ok

    nested = _cfg(
        advisors={"enabled": True, "providers": {"provider": {"api_key": "sk-n"}}}
    )
    assert collect_env_report(nested, env={}).ok


def test_advisors_explicit_openai_provider_requires_key_despite_base_url():
    config = _cfg(
        advisors={
            "enabled": True,
            "providers": {"provider": "openai", "base_url": "http://localhost:1234/v1"},
        }
    )
    report = collect_env_report(config, env={})
    assert [i.var for i in report.missing] == ["OPENAI_API_KEY"]


def test_advisors_custom_base_url_warns_instead_of_failing():
    config = _cfg(
        advisors={
            "enabled": True,
            "providers": {"base_url": "http://localhost:11434/v1"},
        }
    )
    report = collect_env_report(config, env={})
    assert report.ok
    assert [w.var for w in report.warnings] == ["OPENAI_API_KEY"]


def test_validate_logs_recommended_warnings(caplog):
    config = _cfg(
        advisors={
            "enabled": True,
            "providers": {"base_url": "http://localhost:11434/v1"},
        }
    )
    with caplog.at_level(logging.WARNING):
        validate_startup_env(config, env={})  # must not raise
    assert any("OPENAI_API_KEY" in rec.getMessage() for rec in caplog.records)


# ── dograh ───────────────────────────────────────────────────────────────


def test_dograh_actions_without_env_fail_with_both_vars_listed():
    config = _cfg(model_actions=DOGRAH_ACTIONS)
    report = collect_env_report(config, env={})
    assert sorted(i.var for i in report.missing) == [
        "DOGRAH_API_KEY",
        "DOGRAH_BASE_URL",
    ]
    with pytest.raises(EnvValidationError) as exc_info:
        validate_startup_env(config, env={})
    message = str(exc_info.value)
    assert "DOGRAH_BASE_URL" in message
    assert "DOGRAH_API_KEY" in message
    # names the offending commands so users know what enabled the requirement
    assert "call_support" in message
    assert "ring_home" in message


def test_dograh_blank_env_values_count_as_missing():
    config = _cfg(model_actions=DOGRAH_ACTIONS)
    report = collect_env_report(
        config, env={"DOGRAH_BASE_URL": "   ", "DOGRAH_API_KEY": ""}
    )
    assert sorted(i.var for i in report.missing) == [
        "DOGRAH_API_KEY",
        "DOGRAH_BASE_URL",
    ]


def test_dograh_actions_with_env_ok():
    config = _cfg(model_actions=DOGRAH_ACTIONS)
    report = validate_startup_env(
        config,
        env={"DOGRAH_BASE_URL": "http://localhost:8090", "DOGRAH_API_KEY": "dgr_x"},
    )
    assert report.ok


def test_non_dograh_actions_require_nothing():
    config = _cfg(model_actions={"shot": {"action": "keypress", "keys": "x"}})
    assert collect_env_report(config, env={}).ok


# ── aggregation ──────────────────────────────────────────────────────────


def test_all_missing_vars_aggregated_into_one_message():
    config = _cfg(advisors={"enabled": True}, model_actions=DOGRAH_ACTIONS)
    with pytest.raises(EnvValidationError) as exc_info:
        validate_startup_env(config, env={})
    message = str(exc_info.value)
    for var in ("OPENAI_API_KEY", "DOGRAH_BASE_URL", "DOGRAH_API_KEY"):
        assert var in message
    assert message.startswith("Startup aborted")
    assert ".env.example" in message
    assert sorted(exc_info.value.missing_vars) == [
        "DOGRAH_API_KEY",
        "DOGRAH_BASE_URL",
        "OPENAI_API_KEY",
    ]


# ── call sites fail fast ─────────────────────────────────────────────────


def test_cli_main_fails_fast_with_aggregated_message(monkeypatch, capsys):
    """`chatty-commander --web` with advisors enabled and no key exits 1."""
    # `chatty_commander.cli`'s __init__ re-exports the `main` *function*,
    # shadowing the submodule on attribute access — go through importlib.
    import importlib

    main_mod = importlib.import_module("chatty_commander.cli.main")

    fake_config = _cfg(advisors={"enabled": True})
    fake_config.web_server = {}

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(main_mod, "Config", lambda: fake_config)
    monkeypatch.setattr(main_mod, "generate_default_config_if_needed", lambda: False)
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--web"])
    # ModelManager must never be constructed — fail-fast happens before it.
    boom = MagicMock(side_effect=AssertionError("ModelManager should not be built"))
    monkeypatch.setattr(main_mod, "ModelManager", boom)

    assert main_mod.main() == 1
    err = capsys.readouterr().err
    assert "OPENAI_API_KEY" in err
    assert "Startup aborted" in err
    boom.assert_not_called()


def test_cli_cli_main_fails_fast_with_aggregated_message(monkeypatch, capsys):
    import chatty_commander.cli.cli as cli_mod

    fake_config = _cfg(model_actions=dict(DOGRAH_ACTIONS))
    fake_config.web_server = {}

    monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
    monkeypatch.delenv("DOGRAH_API_KEY", raising=False)
    monkeypatch.setattr(cli_mod, "Config", lambda: fake_config)
    monkeypatch.setattr(cli_mod, "generate_default_config_if_needed", lambda: False)
    monkeypatch.setattr(cli_mod, "ModelManager", MagicMock())
    monkeypatch.setattr(cli_mod, "StateManager", MagicMock())
    monkeypatch.setattr(cli_mod, "CommandExecutor", MagicMock())
    monkeypatch.setattr(sys, "argv", ["chatty-commander", "--web"])

    assert cli_mod.cli_main() == 1
    err = capsys.readouterr().err
    assert "DOGRAH_BASE_URL" in err
    assert "DOGRAH_API_KEY" in err


def test_run_server_fails_fast(monkeypatch):
    from chatty_commander.web.web_mode import run_server

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = _cfg(advisors={"enabled": True})
    with pytest.raises(EnvValidationError) as exc_info:
        run_server(config, MagicMock(), MagicMock(), MagicMock())
    assert "OPENAI_API_KEY" in str(exc_info.value)


# ── web auth (BUG 2) ──────────────────────────────────────────────────────


def _web_cfg(*, raw_web=None, resolved_web=None, auth=None):
    """Build a Config-shaped object for the web-auth validator.

    ``config`` is the raw parsed JSON; ``web_server`` is the resolved dict the
    runtime uses. The validator reads both, mirroring the real ``Config``.
    """
    raw = {}
    if raw_web is not None:
        raw["web_server"] = raw_web
    if auth is not None:
        raw["auth"] = auth
    return SimpleNamespace(
        advisors={"enabled": False},
        model_actions={},
        config=raw,
        web_server=resolved_web if resolved_web is not None else {},
    )


def test_explicit_web_auth_enabled_without_key_fails_fast():
    config = _web_cfg(raw_web={"auth_enabled": True}, resolved_web={"auth_enabled": True})
    report = collect_env_report(config, env={}, for_web=True)
    assert [i.var for i in report.missing] == ["CHATTY_API_KEY"]
    with pytest.raises(EnvValidationError) as exc_info:
        validate_startup_env(config, env={}, for_web=True)
    assert "CHATTY_API_KEY" in str(exc_info.value)


def test_web_auth_check_only_runs_for_web_launch():
    """gui/shell/CLI utility modes (for_web=False) must NOT require an API key,
    even when auth_enabled is explicitly true — only the web launch is gated.
    """
    config = _web_cfg(raw_web={"auth_enabled": True}, resolved_web={"auth_enabled": True})
    assert collect_env_report(config, env={}).ok  # default for_web=False
    validate_startup_env(config, env={})  # must not raise


def test_web_auth_enabled_with_env_key_ok():
    config = _web_cfg(raw_web={"auth_enabled": True}, resolved_web={"auth_enabled": True})
    assert collect_env_report(config, env={"CHATTY_API_KEY": "k"}, for_web=True).ok


def test_web_auth_enabled_with_config_key_ok():
    config = _web_cfg(
        raw_web={"auth_enabled": True},
        resolved_web={"auth_enabled": True},
        auth={"api_key": "config-key"},
    )
    assert collect_env_report(config, env={}, for_web=True).ok


def test_default_auth_enabled_does_not_fail_fast():
    """The stock default (auth_enabled True via dataclass default, no explicit
    web_server block in raw config) must NOT require a key — zero-config boots.
    """
    config = _web_cfg(raw_web=None, resolved_web={"auth_enabled": True})
    assert collect_env_report(config, env={}, for_web=True).ok


def test_no_auth_bypass_skips_web_auth_check():
    """--no-auth sets resolved auth_enabled=False even if the file says true:
    the check must not demand a key.
    """
    config = _web_cfg(raw_web={"auth_enabled": True}, resolved_web={"auth_enabled": False})
    assert collect_env_report(config, env={}, for_web=True).ok
