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

"""Token revocation denylist (AUTHZ_DESIGN.md §3, Phase 1).

JWTs are stateless, so logout and refresh-token rotation need a server-side
denylist keyed by the token's ``jti``. This module defines the tiny
:class:`RevocationStore` protocol the verify paths consult and a self-pruning
:class:`InMemoryRevocationStore` default.

The protocol is the seam for a future persistent store (e.g. a sqlite-backed
implementation that survives process restarts). That persistent variant is
explicitly deferred per the design doc (§3 / Phase 4) — only the in-memory
default is built here; nothing else needs to change to swap it in later.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol, runtime_checkable


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
