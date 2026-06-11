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

"""Phase-3 end-to-end through the real app factory (AUTHZ_DESIGN.md §5).

Proves the guarded service-oriented endpoint POST /api/v1/state honors scopes,
and — critically — that the back-compat contract holds: the legacy single key
(wildcard scope) still authenticates; with NO service_keys configured behavior
is identical to today; and DEFAULT / --no-auth flows are byte-for-byte unchanged.
"""

from __future__ import annotations

import bcrypt
import pytest

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.app.config import Config
from chatty_commander.web.deps.auth import get_auth_context
from chatty_commander.web.web_mode import create_app


def _hash(secret: str) -> str:
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.delenv("CHATTY_JWT_SECRET", raising=False)
    monkeypatch.delenv("CHATTY_API_KEY", raising=False)
    get_auth_context().reset()
    yield
    get_auth_context().reset()


def _make_config(auth: dict | None) -> Config:
    cfg = Config(config_file="")
    # Populate state_models so a state change actually succeeds (200); with the
    # empty default the StateManager raises and the handler returns 400, which
    # would mask the auth behavior we are testing.
    cfg.state_models = {"idle": [], "computer": [], "chatty": []}
    if auth is not None:
        cfg.config["auth"] = auth
    return cfg


def _client(auth: dict | None) -> TestClient:
    app = create_app(config=_make_config(auth), no_auth=False)
    return TestClient(app, raise_server_exceptions=False)


# ── back-compat: DEFAULT / --no-auth unchanged ──────────────────────────────


def test_no_key_configured_auth_on_still_401s_unchanged():
    # auth on (no_auth=False) but NO key configured anywhere: the coarse gate
    # cannot authenticate ANY request, exactly as today (constant_time_compare
    # of None vs None is False). require_scope never runs. Back-compat: a
    # service_keys-less server with auth on behaves byte-for-byte as before.
    client = _client(None)
    r = client.post("/api/v1/state", json={"state": "computer"})
    assert r.status_code == 401


def test_no_auth_flag_state_unchanged():
    app = create_app(config=_make_config(None), no_auth=True)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post("/api/v1/state", json={"state": "computer"})
    assert r.status_code == 200


def test_no_service_keys_configured_identical_to_today():
    # Only a legacy api_key, no service_keys block: the wildcard key authenticates
    # and satisfies the state:write scope, exactly as a single global key would.
    client = _client({"api_key": "legacy"})
    r = client.post(
        "/api/v1/state", json={"state": "computer"}, headers={"X-API-Key": "legacy"}
    )
    assert r.status_code == 200
    # Wrong/absent key still 401 (coarse gate unchanged).
    assert client.post("/api/v1/state", json={"state": "computer"}).status_code == 401


# ── legacy single key → wildcard scope passes the scope guard ────────────────


def test_legacy_key_wildcard_satisfies_scope_guard():
    client = _client(
        {
            "api_key": "legacy",
            "service_keys": {
                "scraper": {
                    "key_hash": _hash("scraper-secret"),
                    "scopes": ["status:read"],
                    "active": True,
                }
            },
        }
    )
    r = client.post(
        "/api/v1/state", json={"state": "computer"}, headers={"X-API-Key": "legacy"}
    )
    assert r.status_code == 200


# ── service key scope enforcement on the guarded endpoint ────────────────────


def test_service_key_with_state_write_allowed():
    client = _client(
        {
            "service_keys": {
                "controller": {
                    "key_hash": _hash("ctrl-secret"),
                    "scopes": ["state:write"],
                    "active": True,
                }
            }
        }
    )
    r = client.post(
        "/api/v1/state",
        json={"state": "computer"},
        headers={"X-API-Key": "ctrl-secret"},
    )
    assert r.status_code == 200


def test_service_key_without_state_write_forbidden():
    client = _client(
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
    # Authenticates (valid key) but lacks state:write => 403, not 401.
    r = client.post(
        "/api/v1/state",
        json={"state": "computer"},
        headers={"X-API-Key": "scraper-secret"},
    )
    assert r.status_code == 403


def test_inactive_service_key_rejected_at_gate():
    client = _client(
        {
            "service_keys": {
                "old": {
                    "key_hash": _hash("old-secret"),
                    "scopes": ["state:write"],
                    "active": False,
                }
            }
        }
    )
    r = client.post(
        "/api/v1/state", json={"state": "computer"}, headers={"X-API-Key": "old-secret"}
    )
    # Inactive key never authenticates => coarse 401 (never reaches scope guard).
    assert r.status_code == 401
