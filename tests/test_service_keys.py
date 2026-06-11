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

"""Phase-3 service-key registry + middleware coexistence (AUTHZ_DESIGN.md §5).

Covers the registry/lookup unit surface and the AuthMiddleware integration that
makes the coarse X-API-Key gate accept the legacy single key (→ wildcard scope)
OR any active named service key (→ that key's scopes), attaching the resolved
scopes to ``request.state``.
"""

from __future__ import annotations

import bcrypt
import pytest

try:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.middleware.auth import AuthMiddleware
from chatty_commander.web.middleware.service_keys import (
    resolve_service_key_scopes,
    service_keys_config,
)


def _hash(secret: str) -> str:
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=4)).decode()


class _Cfg:
    """Minimal Config-shaped object: ``.config['auth']`` dict lookup."""

    def __init__(self, auth: dict) -> None:
        self.config = {"auth": auth}


@pytest.fixture(autouse=True)
def _no_env_key(monkeypatch):
    monkeypatch.delenv("CHATTY_API_KEY", raising=False)
    yield


# ── registry / lookup unit tests ────────────────────────────────────────────


def test_no_service_keys_block_returns_none():
    cfg = _Cfg({"api_key": "legacy"})
    assert service_keys_config(cfg) == {}
    assert resolve_service_key_scopes(cfg, "anything") is None


def test_active_service_key_resolves_its_scopes():
    cfg = _Cfg(
        {
            "service_keys": {
                "scraper": {
                    "key_hash": _hash("scraper-secret"),
                    "scopes": ["status:read"],
                    "active": True,
                }
            }
        }
    )
    assert resolve_service_key_scopes(cfg, "scraper-secret") == ["status:read"]


def test_inactive_service_key_is_rejected():
    cfg = _Cfg(
        {
            "service_keys": {
                "old": {
                    "key_hash": _hash("old-secret"),
                    "scopes": ["command:write"],
                    "active": False,
                }
            }
        }
    )
    # The hash is on file but the key is rotated out: no match.
    assert resolve_service_key_scopes(cfg, "old-secret") is None


def test_wrong_secret_does_not_match():
    cfg = _Cfg(
        {
            "service_keys": {
                "bridge": {
                    "key_hash": _hash("right-secret"),
                    "scopes": ["command:write"],
                    "active": True,
                }
            }
        }
    )
    assert resolve_service_key_scopes(cfg, "wrong-secret") is None


def test_blank_or_missing_key_returns_none():
    cfg = _Cfg(
        {"service_keys": {"x": {"key_hash": _hash("s"), "scopes": [], "active": True}}}
    )
    assert resolve_service_key_scopes(cfg, None) is None
    assert resolve_service_key_scopes(cfg, "") is None


def test_active_key_with_no_scopes_resolves_empty_list():
    cfg = _Cfg({"service_keys": {"x": {"key_hash": _hash("s"), "active": True}}})
    # Distinguishable from None (no match): an empty list means "matched, no scopes".
    assert resolve_service_key_scopes(cfg, "s") == []


def test_malformed_spec_is_skipped():
    cfg = _Cfg(
        {
            "service_keys": {
                "bad": "not-a-dict",
                "good": {
                    "key_hash": _hash("good-secret"),
                    "scopes": ["status:read"],
                    "active": True,
                },
            }
        }
    )
    assert resolve_service_key_scopes(cfg, "good-secret") == ["status:read"]


# ── AuthMiddleware coexistence (legacy key OR service key) ───────────────────


def _app(auth: dict) -> TestClient:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=_Cfg(auth))

    @app.get("/api/echo-scopes")
    async def echo(request: Request):
        return {"scopes": getattr(request.state, "scopes", None)}

    return TestClient(app, raise_server_exceptions=False)


def test_legacy_key_authenticates_with_wildcard_scope():
    client = _app({"api_key": "legacy"})
    r = client.get("/api/echo-scopes", headers={"X-API-Key": "legacy"})
    assert r.status_code == 200
    assert r.json()["scopes"] == ["*"]


def test_service_key_authenticates_and_carries_scopes():
    client = _app(
        {
            "service_keys": {
                "scraper": {
                    "key_hash": _hash("scraper-secret"),
                    "scopes": ["status:read"],
                    "active": True,
                }
            }
        }
    )
    r = client.get("/api/echo-scopes", headers={"X-API-Key": "scraper-secret"})
    assert r.status_code == 200
    assert r.json()["scopes"] == ["status:read"]


def test_legacy_and_service_keys_coexist():
    client = _app(
        {
            "api_key": "legacy",
            "service_keys": {
                "bridge": {
                    "key_hash": _hash("bridge-secret"),
                    "scopes": ["command:write"],
                    "active": True,
                }
            },
        }
    )
    # Legacy key → wildcard.
    r1 = client.get("/api/echo-scopes", headers={"X-API-Key": "legacy"})
    assert r1.status_code == 200 and r1.json()["scopes"] == ["*"]
    # Service key → its scopes.
    r2 = client.get("/api/echo-scopes", headers={"X-API-Key": "bridge-secret"})
    assert r2.status_code == 200 and r2.json()["scopes"] == ["command:write"]


def test_inactive_service_key_rejected_by_middleware():
    client = _app(
        {
            "service_keys": {
                "old": {
                    "key_hash": _hash("old-secret"),
                    "scopes": ["command:write"],
                    "active": False,
                }
            }
        }
    )
    r = client.get("/api/echo-scopes", headers={"X-API-Key": "old-secret"})
    assert r.status_code == 401


def test_unknown_key_rejected_when_keys_configured():
    client = _app(
        {
            "api_key": "legacy",
            "service_keys": {
                "bridge": {
                    "key_hash": _hash("bridge-secret"),
                    "scopes": ["command:write"],
                    "active": True,
                }
            },
        }
    )
    r = client.get("/api/echo-scopes", headers={"X-API-Key": "nope"})
    assert r.status_code == 401
