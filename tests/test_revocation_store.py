"""Unit tests for the jti revocation denylist (AUTHZ_DESIGN.md §3).

The store is the seam a future persistent (sqlite) implementation plugs into,
so these tests pin the Protocol contract: revoke -> is_revoked, expiry-based
self-pruning (driven by a mocked clock, no real sleeps).
"""

from __future__ import annotations

from chatty_commander.web.revocation import (
    InMemoryRevocationStore,
    RevocationStore,
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
