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

"""Token revocation denylist (AUTHZ_DESIGN.md §3, Phases 1 & 4).

JWTs are stateless, so logout and refresh-token rotation need a server-side
denylist keyed by the token's ``jti``. This module defines the tiny
:class:`RevocationStore` protocol the verify paths consult and two
implementations:

- :class:`InMemoryRevocationStore` (default) — a self-pruning, process-local
  ``{jti: exp}`` dict. Revocations are lost on restart, which only loses
  *early* revocations (tokens expire on their own) — acceptable for the
  local-first threat model (§3).
- :class:`SqliteRevocationStore` (Phase 4, opt-in) — a sqlite-backed denylist
  for users who want revocations to survive a process restart. Same
  self-pruning contract; selected via ``auth.revocation_store: "sqlite"``.

Both satisfy the same :class:`RevocationStore` protocol, so the store can be
swapped in :mod:`chatty_commander.web.server` without touching the verify paths.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time
from collections.abc import Callable
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Default on-disk location for the sqlite store, relative to cwd. Kept small and
# hidden so it sits alongside other ``.chatty`` runtime state.
DEFAULT_SQLITE_PATH = ".chatty/revocations.sqlite3"


@runtime_checkable
class RevocationStore(Protocol):
    """A jti denylist.

    Implementations key on a token's ``jti`` and remember its ``exp`` (unix
    timestamp) so revoked entries can be pruned once the token would have
    expired on its own. This is the seam a persistent (sqlite/JSON) store can
    implement later without touching the verify paths.
    """

    def revoke(self, jti: str, exp: int) -> None:
        """Mark ``jti`` revoked until its ``exp`` (unix ts) passes."""
        ...

    def is_revoked(self, jti: str) -> bool:
        """Return True if ``jti`` is currently revoked (and not yet expired)."""
        ...


class InMemoryRevocationStore:
    """Process-local jti denylist with lazy pruning by ``exp``.

    Backed by a ``{jti: exp}`` dict guarded by a lock. Entries past their
    ``exp`` are dropped lazily on access (same self-pruning pattern as
    ``TokenBucketRateLimiter._prune_locked``), so the table never grows beyond
    the set of *currently-valid* revoked tokens.

    Adequate for a single-process local-first server: tokens naturally expire,
    so a process restart only loses *early* revocations — acceptable for this
    threat model (design §3).
    """

    def __init__(self, *, time_fn: Callable[[], float] = time.time) -> None:
        self._time_fn = time_fn
        self._lock = threading.Lock()
        self._revoked: dict[str, int] = {}

    def revoke(self, jti: str, exp: int) -> None:
        if not jti:
            return
        now = int(self._time_fn())
        with self._lock:
            self._revoked[jti] = int(exp)
            self._prune_locked(now)

    def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        now = int(self._time_fn())
        with self._lock:
            exp = self._revoked.get(jti)
            if exp is None:
                return False
            if exp <= now:
                # Token would have expired anyway; drop and treat as not revoked.
                del self._revoked[jti]
                return False
            return True

    def _prune_locked(self, now: int) -> None:
        """Drop entries whose token has already expired."""
        stale = [jti for jti, exp in self._revoked.items() if exp <= now]
        for jti in stale:
            del self._revoked[jti]

    def __len__(self) -> int:  # pragma: no cover - trivial, aids testing
        with self._lock:
            return len(self._revoked)

    def close(self) -> None:  # pragma: no cover - trivial, no connection to close
        """No-op: the in-memory store holds no connection. Idempotent.

        Defined so callers (e.g. the app-shutdown hook) can ``close()`` either
        backend uniformly without a ``hasattr`` branch.
        """
        return None


class SqliteRevocationStore:
    """Persistent jti denylist backed by sqlite, with pruning by ``exp``.

    Stores ``(jti, exp)`` rows in a single table keyed on ``jti``. Unlike
    :class:`InMemoryRevocationStore`, revocations survive a process restart:
    point a fresh instance at the same database file and previously-revoked
    (still-valid) tokens remain revoked.

    Self-pruning happens on the *write* path only: :meth:`revoke` upserts then
    deletes every row past its ``exp`` (and :meth:`prune` can be called
    explicitly), so the table never grows beyond the set of *currently-valid*
    revoked tokens. :meth:`is_revoked` is a pure read — it never writes — so the
    hot auth path is not serialized behind a write lock + fsync; an expired row
    reads as not-revoked without being deleted.

    Thread safety: a single connection opened with ``check_same_thread=False``
    is guarded by a lock, so the store is safe to share across the request
    threads that consult it. Pass ``path=":memory:"`` for an ephemeral in-memory
    database (used by tests); any other path is created (with parent dirs) on
    first use.

    Note: a ``:memory:`` path cannot persist across the per-app store rebuilds
    in ``server.register_shared_routers`` (defeating the "survives restart"
    contract), so configuring it outside tests logs a warning.
    """

    def __init__(
        self,
        path: str = DEFAULT_SQLITE_PATH,
        *,
        time_fn: Callable[[], float] = time.time,
    ) -> None:
        self._time_fn = time_fn
        self._lock = threading.Lock()
        self._closed = False
        if path == ":memory:":
            # ``:memory:`` databases are per-connection and vanish on close, so a
            # fresh store (e.g. a new app instance) can't see prior revocations —
            # this silently defeats the Phase 4 "survives restart" contract.
            logger.warning(
                "SqliteRevocationStore configured with ':memory:'; revocations "
                "will not persist across process restarts or app rebuilds. Use a "
                "file path for the persistence the sqlite backend is meant to "
                "provide."
            )
        else:
            import os

            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        # One shared connection guarded by ``self._lock``; ``:memory:`` databases
        # are per-connection, so we must keep this handle alive for its lifetime.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS revoked_tokens "
                "(jti TEXT PRIMARY KEY, exp INTEGER NOT NULL)"
            )
            self._conn.commit()

    def revoke(self, jti: str, exp: int) -> None:
        if not jti:
            return
        now = int(self._time_fn())
        with self._lock:
            self._conn.execute(
                "INSERT INTO revoked_tokens (jti, exp) VALUES (?, ?) "
                "ON CONFLICT(jti) DO UPDATE SET exp=excluded.exp",
                (jti, int(exp)),
            )
            self._prune_locked(now)
            self._conn.commit()

    def is_revoked(self, jti: str) -> bool:
        # Pure read: SELECT only, never writes. Returns True iff the jti exists
        # and its token has not yet expired. Expired rows read as not-revoked but
        # are left for :meth:`revoke`/:meth:`prune` to clean up, so the hot auth
        # path is not serialized behind a write lock + fsync.
        if not jti:
            return False
        now = int(self._time_fn())
        with self._lock:
            row = self._conn.execute(
                "SELECT exp FROM revoked_tokens WHERE jti = ? AND exp > ?",
                (jti, now),
            ).fetchone()
            return row is not None

    def prune(self) -> None:
        """Drop rows whose token has already expired (write path)."""
        now = int(self._time_fn())
        with self._lock:
            self._prune_locked(now)
            self._conn.commit()

    def _prune_locked(self, now: int) -> None:
        """Drop rows whose token has already expired (caller holds the lock)."""
        self._conn.execute("DELETE FROM revoked_tokens WHERE exp <= ?", (now,))

    def __len__(self) -> int:  # pragma: no cover - trivial, aids testing
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM revoked_tokens").fetchone()
            return int(row[0]) if row else 0

    def close(self) -> None:
        """Close the underlying sqlite connection. Idempotent."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._conn.close()
