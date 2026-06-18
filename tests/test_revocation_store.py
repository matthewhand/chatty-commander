"""Unit tests for the jti revocation denylist (AUTHZ_DESIGN.md §3).

The store is the seam a future persistent (sqlite) implementation plugs into,
so these tests pin the Protocol contract: revoke -> is_revoked, expiry-based
self-pruning (driven by a mocked clock, no real sleeps).
"""

from __future__ import annotations

import pytest

from chatty_commander.web.revocation import (
    InMemoryRevocationStore,
    RevocationStore,
    SqliteRevocationStore,
)


class _Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def test_default_store_satisfies_protocol():
    assert isinstance(InMemoryRevocationStore(), RevocationStore)


def test_revoke_then_is_revoked():
    clock = _Clock()
    store = InMemoryRevocationStore(time_fn=clock)
    store.revoke("jti-1", exp=int(clock.t) + 100)
    assert store.is_revoked("jti-1") is True
    assert store.is_revoked("never-revoked") is False


def test_is_revoked_false_after_token_expiry_and_entry_dropped():
    clock = _Clock(t=1000.0)
    store = InMemoryRevocationStore(time_fn=clock)
    store.revoke("jti-1", exp=1100)
    assert store.is_revoked("jti-1") is True
    # Advance past the token's own exp: it's no longer "revoked" (it's dead) and
    # the lookup prunes the entry.
    clock.t = 1101.0
    assert store.is_revoked("jti-1") is False
    assert len(store) == 0


def test_revoke_self_prunes_expired_entries():
    clock = _Clock(t=1000.0)
    store = InMemoryRevocationStore(time_fn=clock)
    store.revoke("short", exp=1050)
    store.revoke("long", exp=5000)
    assert len(store) == 2
    # Advance past 'short' exp, then revoke another: the expired entry is pruned
    # so the table never grows beyond currently-valid revoked tokens.
    clock.t = 1051.0
    store.revoke("new", exp=6000)
    assert store.is_revoked("short") is False
    assert store.is_revoked("long") is True
    assert store.is_revoked("new") is True
    assert len(store) == 2


def test_empty_jti_is_noop_and_not_revoked():
    store = InMemoryRevocationStore()
    store.revoke("", exp=9999999999)
    assert store.is_revoked("") is False
    assert len(store) == 0


# ── SqliteRevocationStore (Phase 4) ─────────────────────────────────────────


def test_sqlite_store_satisfies_protocol():
    assert isinstance(SqliteRevocationStore(":memory:"), RevocationStore)


def test_sqlite_revoke_then_is_revoked():
    clock = _Clock()
    store = SqliteRevocationStore(":memory:", time_fn=clock)
    store.revoke("jti-1", exp=int(clock.t) + 100)
    assert store.is_revoked("jti-1") is True
    assert store.is_revoked("never-revoked") is False


def test_sqlite_is_revoked_false_after_token_expiry_and_entry_dropped():
    clock = _Clock(t=1000.0)
    store = SqliteRevocationStore(":memory:", time_fn=clock)
    store.revoke("jti-1", exp=1100)
    assert store.is_revoked("jti-1") is True
    clock.t = 1101.0
    assert store.is_revoked("jti-1") is False
    assert len(store) == 0


def test_sqlite_revoke_self_prunes_expired_entries():
    clock = _Clock(t=1000.0)
    store = SqliteRevocationStore(":memory:", time_fn=clock)
    store.revoke("short", exp=1050)
    store.revoke("long", exp=5000)
    assert len(store) == 2
    clock.t = 1051.0
    store.revoke("new", exp=6000)
    assert store.is_revoked("short") is False
    assert store.is_revoked("long") is True
    assert store.is_revoked("new") is True
    assert len(store) == 2


def test_sqlite_revoke_upserts_existing_jti():
    clock = _Clock(t=1000.0)
    store = SqliteRevocationStore(":memory:", time_fn=clock)
    store.revoke("jti-1", exp=1100)
    # Re-revoking the same jti updates exp in place (no duplicate row).
    store.revoke("jti-1", exp=2000)
    assert len(store) == 1
    clock.t = 1500.0
    assert store.is_revoked("jti-1") is True


def test_sqlite_empty_jti_is_noop_and_not_revoked():
    store = SqliteRevocationStore(":memory:")
    store.revoke("", exp=9999999999)
    assert store.is_revoked("") is False
    assert len(store) == 0


def test_sqlite_revocation_persists_across_instances(tmp_path):
    """A fresh store on the same file still sees a revoked token (Phase 4 goal)."""
    db = str(tmp_path / "revocations.sqlite3")
    clock = _Clock(t=1000.0)
    store = SqliteRevocationStore(db, time_fn=clock)
    store.revoke("jti-persist", exp=5000)
    store.close()

    # New instance, same file, same (still-valid) clock: revocation survives.
    reopened = SqliteRevocationStore(db, time_fn=clock)
    assert reopened.is_revoked("jti-persist") is True
    assert reopened.is_revoked("other") is False
    reopened.close()


def test_sqlite_creates_parent_directory(tmp_path):
    db = str(tmp_path / "nested" / "dir" / "revocations.sqlite3")
    store = SqliteRevocationStore(db)
    store.revoke("jti-1", exp=9999999999)
    assert store.is_revoked("jti-1") is True
    store.close()


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
def test_server_selects_revocation_store_from_config(kind, tmp_path):
    """``auth.revocation_store`` selects the backing store in the app factory."""
    from types import SimpleNamespace

    from chatty_commander.web.deps.auth import get_auth_context
    from chatty_commander.web.server import create_app

    auth_cfg: dict = {
        "users": {"alice": {"password_hash": "x", "roles": ["user"]}},
        "jwt_secret": "wiring-test-secret",
        "revocation_store": kind,
    }
    if kind == "sqlite":
        auth_cfg["revocation_store_path"] = str(tmp_path / "rev.sqlite3")

    get_auth_context().reset()
    try:
        create_app(no_auth=False, config_manager=SimpleNamespace(auth=auth_cfg))
        store = get_auth_context().revocation_store
        expected = (
            "SqliteRevocationStore" if kind == "sqlite" else "InMemoryRevocationStore"
        )
        assert type(store).__name__ == expected
    finally:
        get_auth_context().reset()
