"""Startup validation of environment variables for explicitly enabled features.

ROADMAP item "Secrets validation at startup": fail fast — with one aggregated,
actionable message — when env vars that an *enabled* feature requires are
missing. Two hard rules keep this safe:

1. **Zero-config boots.** Nothing is required when features are off; a default
   config with no environment variables set must always start.
2. **Required vs recommended.** Only vars a feature cannot work without are
   fatal. Recommended-but-optional gaps are logged as warnings, never fatal.

Current rules:

- Advisors enabled (``advisors.enabled``) and backed by OpenAI (explicit
  ``provider: openai`` or no custom ``base_url``) with no API key configured
  anywhere → ``OPENAI_API_KEY`` is required.
- Advisors enabled with a custom non-OpenAI ``base_url`` and no API key →
  warning only (local OpenAI-compatible servers often need no key).
- Any command configured with a ``dograh_call`` action → ``DOGRAH_BASE_URL``
  and ``DOGRAH_API_KEY`` are required (see ``integrations/dograh_client.py``).
- Web auth enabled (``web_server.auth_enabled``) with no API key configured
  anywhere (``CHATTY_API_KEY`` env or ``auth.api_key`` config) → ``CHATTY_API_KEY``
  is required. Without it the middleware would silently 401 every request.

All checks are defensive about config shape (tests inject mocks/partial
configs); anything that is not a real dict is treated as "feature off".
Every consumed env var is documented in ``.env.example``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvIssue:
    """A single missing/recommended environment variable for a feature."""

    var: str
    feature: str
    reason: str

    def __str__(self) -> str:
        return f"{self.var} ({self.feature}): {self.reason}"


@dataclass
class EnvReport:
    """Aggregated result of startup environment validation."""

    missing: list[EnvIssue] = field(default_factory=list)
    warnings: list[EnvIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing

    def error_message(self) -> str:
        lines = [
            "Startup aborted: missing required environment variables for enabled features:"
        ]
        lines += [f"  - {issue}" for issue in self.missing]
        lines.append(
            "Set the variables above (see .env.example) or disable the feature(s) in your config."
        )
        return "\n".join(lines)


class EnvValidationError(RuntimeError):
    """Raised at startup when required env vars for enabled features are missing.

    ``str(error)`` is the aggregated, user-facing message listing every
    missing variable, so callers can print it and exit.
    """

    def __init__(self, report: EnvReport) -> None:
        self.report = report
        self.missing_vars = [issue.var for issue in report.missing]
        super().__init__(report.error_message())


def _as_dict(value: Any) -> dict[str, Any]:
    """Return ``value`` if it is a real dict, else {} (mock/shape tolerant)."""
    return value if isinstance(value, dict) else {}


def _env_set(env: Mapping[str, str], var: str) -> bool:
    """True when ``var`` is present and non-blank (empty string == unset)."""
    value = env.get(var)
    return isinstance(value, str) and bool(value.strip())


def _check_advisors(config: Any, env: Mapping[str, str], report: EnvReport) -> None:
    advisors = _as_dict(getattr(config, "advisors", None))
    if not advisors.get("enabled", False):
        return

    providers = _as_dict(advisors.get("providers"))
    nested = providers.get("provider")
    nested_cfg = _as_dict(nested)
    provider_name = nested if isinstance(nested, str) else nested_cfg.get("name")

    api_key = providers.get("api_key") or nested_cfg.get("api_key")
    if api_key or _env_set(env, "OPENAI_API_KEY"):
        return

    base_url = providers.get("base_url") or nested_cfg.get("base_url")
    is_openai = (
        (isinstance(provider_name, str) and provider_name.lower() == "openai")
        or not isinstance(base_url, str)
        or not base_url.strip()
        or "openai" in base_url
    )
    if is_openai:
        report.missing.append(
            EnvIssue(
                var="OPENAI_API_KEY",
                feature="advisors",
                reason=(
                    "advisors are enabled with the OpenAI provider but no API key "
                    "is configured (advisors.providers.api_key) or exported"
                ),
            )
        )
    else:
        report.warnings.append(
            EnvIssue(
                var="OPENAI_API_KEY",
                feature="advisors",
                reason=(
                    f"advisors use custom base_url {base_url!r} with no API key; "
                    "set OPENAI_API_KEY if that endpoint requires authentication"
                ),
            )
        )


def _check_dograh(config: Any, env: Mapping[str, str], report: EnvReport) -> None:
    model_actions = _as_dict(getattr(config, "model_actions", None))
    dograh_commands = sorted(
        name
        for name, action in model_actions.items()
        if _as_dict(action).get("action") == "dograh_call"
    )
    if not dograh_commands:
        return

    commands_desc = ", ".join(dograh_commands)
    for var in ("DOGRAH_BASE_URL", "DOGRAH_API_KEY"):
        if not _env_set(env, var):
            report.missing.append(
                EnvIssue(
                    var=var,
                    feature="dograh",
                    reason=(
                        f"command(s) configured with 'dograh_call' actions ({commands_desc}) "
                        "need the dograh API; see docker-compose.dograh.yml"
                    ),
                )
            )


def _check_web_auth(config: Any, env: Mapping[str, str], report: EnvReport) -> None:
    """Require an API key when web auth is *explicitly* enabled but none is set.

    The middleware only authenticates when an expected key exists. If a user
    turns auth on yet configures no key (via ``CHATTY_API_KEY`` or
    ``auth.api_key``), every ``/api`` request would 401 silently — so we fail
    fast at startup with an actionable message instead.

    Two invariants keep this safe:

    * **Zero-config boots.** ``web_server.auth_enabled`` defaults to ``True`` in
      ``Config`` even when the user wrote no config at all, so the bare default
      must NOT trip this check. We therefore only fire when the user
      *explicitly* set ``web_server.auth_enabled: true`` in their raw config
      (``config.config["web_server"]``) — the stock default carries no
      ``web_server`` block and is left untouched.
    * **--no-auth bypass.** The dev bypass sets ``auth_enabled=False`` before
      validating (see CLI entrypoints and ``web_mode.run_web_server``), so it
      never reaches this check.
    """
    # The --no-auth bypass sets auth_enabled=False on the *resolved*
    # web_server dict (CLI entrypoints + web_mode.run_web_server). Honor that
    # first so a config file with auth_enabled:true + --no-auth never trips.
    resolved_web = _as_dict(getattr(config, "web_server", None))
    if resolved_web.get("auth_enabled") is False:
        return

    raw = _as_dict(getattr(config, "config", None))
    raw_web = raw.get("web_server")
    # Only an *explicit* auth_enabled:true in the user's config triggers the
    # requirement; the dataclass default must keep the zero-config boot clean.
    if not (isinstance(raw_web, dict) and raw_web.get("auth_enabled") is True):
        return

    if _env_set(env, "CHATTY_API_KEY"):
        return

    auth_cfg = raw.get("auth")
    if not isinstance(auth_cfg, dict):
        # Tolerate DummyConfig.auth too.
        auth_cfg = _as_dict(getattr(config, "auth", None))
    api_key = auth_cfg.get("api_key") if isinstance(auth_cfg, dict) else None
    if api_key:
        return

    report.missing.append(
        EnvIssue(
            var="CHATTY_API_KEY",
            feature="web auth",
            reason=(
                "web_server.auth_enabled is true but no API key is configured "
                "via CHATTY_API_KEY or auth.api_key; the server would reject "
                "every /api request. Set CHATTY_API_KEY or run with --no-auth"
            ),
        )
    )


def collect_env_report(
    config: Any, env: Mapping[str, str] | None = None, *, for_web: bool = False
) -> EnvReport:
    """Inspect ``config`` and ``env`` and report missing/recommended env vars.

    Pure (no logging, no raising); use :func:`validate_startup_env` at call
    sites that want fail-fast behavior.

    ``for_web`` enables the web-auth check, which is only meaningful when the
    web server is actually being launched (gui/shell/CLI utility modes must not
    be gated by a missing API key).
    """
    if env is None:
        env = os.environ
    report = EnvReport()
    _check_advisors(config, env, report)
    _check_dograh(config, env, report)
    if for_web:
        _check_web_auth(config, env, report)
    return report


def validate_startup_env(
    config: Any,
    env: Mapping[str, str] | None = None,
    log: logging.Logger | None = None,
    *,
    for_web: bool = False,
) -> EnvReport:
    """Validate env vars for enabled features; fail fast when required ones are missing.

    Logs each recommended-but-optional gap at WARNING level, then raises
    :class:`EnvValidationError` (whose message aggregates *all* missing vars)
    if any required variable is absent. Returns the report when everything
    required is present.

    Pass ``for_web=True`` from the web-server launch path to additionally
    require a web API key when ``web_server.auth_enabled`` is explicitly set.
    """
    report = collect_env_report(config, env, for_web=for_web)
    log = log or logger
    for issue in report.warnings:
        log.warning("Optional env var not set: %s", issue)
    if not report.ok:
        raise EnvValidationError(report)
    return report
