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

"""Rate limiting on POST /api/v1/command (topic from bot PR #639).

Covers the dependency-free in-memory token bucket and its wiring into the
command endpoint: per-key budgets, refill over time, 429 + Retry-After on
exhaustion, env-based configuration, and the default-off behavior under
pytest so existing suites are unaffected.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.core import (
    DEFAULT_COMMAND_RATE_LIMIT_PER_MINUTE,
    TokenBucketRateLimiter,
    _resolve_command_rate_limit,
    include_core_routes,
)

# ---------------------------------------------------------------------------
# Token bucket unit tests
# ---------------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_bucket_allows_burst_then_denies():
    clock = FakeClock()
    limiter = TokenBucketRateLimiter(3, time_fn=clock)
    assert all(limiter.try_acquire("k")[0] for _ in range(3))
    allowed, retry_after = limiter.try_acquire("k")
    assert allowed is False
    assert retry_after > 0


def test_bucket_refills_over_time():
    clock = FakeClock()
    limiter = TokenBucketRateLimiter(60, time_fn=clock)  # 1 token/second
    for _ in range(60):
        assert limiter.try_acquire("k")[0]
    assert limiter.try_acquire("k")[0] is False
    clock.advance(1.0)  # exactly one token refilled
    assert limiter.try_acquire("k")[0] is True
    assert limiter.try_acquire("k")[0] is False


def test_bucket_keys_are_independent():
    clock = FakeClock()
    limiter = TokenBucketRateLimiter(1, time_fn=clock)
    assert limiter.try_acquire("a")[0] is True
    assert limiter.try_acquire("a")[0] is False
    assert limiter.try_acquire("b")[0] is True


def test_bucket_retry_after_matches_refill_rate():
    clock = FakeClock()
    limiter = TokenBucketRateLimiter(60, time_fn=clock)  # 1 token/second
    for _ in range(60):
        limiter.try_acquire("k")
    _, retry_after = limiter.try_acquire("k")
    # Plain tolerance check (not pytest.approx: other suites leave a stubbed
    # numpy module in sys.modules which breaks approx's numpy detection).
    assert abs(retry_after - 1.0) < 1e-9


def test_bucket_prunes_idle_keys():
    clock = FakeClock()
    limiter = TokenBucketRateLimiter(60, time_fn=clock, max_keys=10)
    for i in range(10):
        limiter.try_acquire(f"old-{i}")
    clock.advance(120.0)  # all old buckets fully refilled -> prunable
    limiter.try_acquire("new")
    assert len(limiter._buckets) <= 11
    assert "new" in limiter._buckets
    assert not any(k.startswith("old-") for k in limiter._buckets)


def test_bucket_rejects_nonpositive_rate():
    with pytest.raises(ValueError):
        TokenBucketRateLimiter(0)


# ---------------------------------------------------------------------------
# Env resolution
# ---------------------------------------------------------------------------


def test_resolve_explicit_limit(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "12")
    assert _resolve_command_rate_limit() == 12.0


@pytest.mark.parametrize("value", ["0", "off", "OFF", "false", "disabled", "none"])
def test_resolve_disabled_values(monkeypatch, value):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", value)
    assert _resolve_command_rate_limit() is None


def test_resolve_invalid_value_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "not-a-number")
    assert _resolve_command_rate_limit() == DEFAULT_COMMAND_RATE_LIMIT_PER_MINUTE


def test_resolve_unset_disabled_under_pytest(monkeypatch):
    monkeypatch.delenv("CHATCOMM_COMMAND_RATE_LIMIT", raising=False)
    # PYTEST_CURRENT_TEST is set by pytest itself while this test runs.
    assert _resolve_command_rate_limit() is None


def test_resolve_unset_defaults_outside_test_mode(monkeypatch):
    monkeypatch.delenv("CHATCOMM_COMMAND_RATE_LIMIT", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert _resolve_command_rate_limit() == DEFAULT_COMMAND_RATE_LIMIT_PER_MINUTE


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "ON"])
def test_resolve_explicit_optout_disables(monkeypatch, value):
    """CHATTY_DISABLE_RATE_LIMIT is an explicit, unambiguous opt-out."""
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "30")
    monkeypatch.setenv("CHATTY_DISABLE_RATE_LIMIT", value)
    assert _resolve_command_rate_limit() is None


def test_resolve_explicit_optout_falsey_does_not_disable(monkeypatch):
    """A non-truthy CHATTY_DISABLE_RATE_LIMIT must not disable the limiter."""
    monkeypatch.delenv("CHATCOMM_COMMAND_RATE_LIMIT", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("CHATTY_DISABLE_RATE_LIMIT", "0")
    assert _resolve_command_rate_limit() == DEFAULT_COMMAND_RATE_LIMIT_PER_MINUTE


# ---------------------------------------------------------------------------
# Endpoint integration
# ---------------------------------------------------------------------------


def _make_client() -> TestClient:
    app = FastAPI()
    state_manager = SimpleNamespace(current_state="idle", get_active_models=lambda: [])
    router = include_core_routes(
        get_start_time=lambda: 0.0,
        get_state_manager=lambda: state_manager,
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=datetime.now,
        execute_command_fn=lambda name: True,
    )
    app.include_router(router)
    return TestClient(app)


def test_endpoint_returns_429_after_limit(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "3")
    client = _make_client()
    for _ in range(3):
        resp = client.post("/api/v1/command", json={"command": "hello"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
    resp = client.post("/api/v1/command", json={"command": "hello"})
    assert resp.status_code == 429
    assert "Rate limit" in resp.json()["detail"]
    assert int(resp.headers["Retry-After"]) >= 1


def test_endpoint_rate_limit_is_per_api_key(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "1")
    client = _make_client()
    assert (
        client.post(
            "/api/v1/command",
            json={"command": "a"},
            headers={"X-API-Key": "alice"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/command",
            json={"command": "a"},
            headers={"X-API-Key": "alice"},
        ).status_code
        == 429
    )
    # A different key has its own budget.
    assert (
        client.post(
            "/api/v1/command",
            json={"command": "a"},
            headers={"X-API-Key": "bob"},
        ).status_code
        == 200
    )


def test_endpoint_unlimited_by_default_under_pytest(monkeypatch):
    monkeypatch.delenv("CHATCOMM_COMMAND_RATE_LIMIT", raising=False)
    client = _make_client()
    for _ in range(50):
        resp = client.post("/api/v1/command", json={"command": "hello"})
        assert resp.status_code == 200


def test_endpoint_explicit_off_disables_limit(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "off")
    client = _make_client()
    for _ in range(50):
        resp = client.post("/api/v1/command", json={"command": "hello"})
        assert resp.status_code == 200


def test_other_endpoints_not_rate_limited(monkeypatch):
    monkeypatch.setenv("CHATCOMM_COMMAND_RATE_LIMIT", "1")
    client = _make_client()
    assert client.post("/api/v1/command", json={"command": "a"}).status_code == 200
    assert client.post("/api/v1/command", json={"command": "a"}).status_code == 429
    # Read-only endpoints stay available.
    for _ in range(5):
        assert client.get("/api/v1/status").status_code == 200
        assert client.get("/api/v1/metrics").status_code == 200
