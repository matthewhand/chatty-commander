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

from __future__ import annotations

import json
import logging
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    role: str  # "user" | "assistant"
    content: str
    timestamp: str


class MemoryStore:
    def __init__(
        self,
        max_items_per_context: int = 100,
        persist: bool = False,
        persist_path: str | None = None,
        compact_every: int = 500,
    ) -> None:
        self._store: dict[str, deque[MemoryItem]] = {}
        self._max = max(1, int(max_items_per_context))
        self._persist = persist
        self._path = persist_path or "data/advisors_memory.jsonl"
        # Compact the on-disk JSONL after this many appends so the file does
        # not grow unbounded (in-memory deques are already capped at ``_max``).
        self._compact_every = max(1, int(compact_every))
        self._appends_since_compact = 0
        if self._persist:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load memory from the persistence file."""
        if not os.path.exists(self._path):
            return

        try:
            with open(self._path, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        key = data.get("key")
                        if key:
                            q = self._store.setdefault(key, deque(maxlen=self._max))
                            q.append(
                                MemoryItem(
                                    role=data["role"],
                                    content=data["content"],
                                    timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
                                )
                            )
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            logger.warning("Failed to load advisor memory from %s: %s", self._path, e)

    def _ctx(self, platform: str, channel: str, user: str) -> str:
        return f"{platform}:{channel}:{user}"

    def add(
        self, platform: str, channel: str, user: str, role: str, content: str
    ) -> None:
        """Add memory item for context."""
        key = self._ctx(platform, channel, user)
        q = self._store.setdefault(key, deque(maxlen=self._max))
        ts = datetime.utcnow().isoformat()
        q.append(
            MemoryItem(
                role=role, content=content, timestamp=ts
            )
        )
        if self._persist:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "key": key,
                                "role": role,
                                "content": content,
                                "timestamp": ts,
                            }
                        )
                        + "\n"
                    )
                self._appends_since_compact += 1
                if self._appends_since_compact >= self._compact_every:
                    self.compact()
            except Exception as e:
                logger.warning("Failed to persist advisor memory to %s: %s", self._path, e)

    def get(
        self, platform: str, channel: str, user: str, limit: int = 20
    ) -> list[MemoryItem]:
        """Get recent memory items for context."""
        key = self._ctx(platform, channel, user)
        items = list(self._store.get(key, deque()))
        if limit <= 0:
            return []
        return items[-limit:]

    def clear(self, platform: str, channel: str, user: str) -> int:
        """Clear memory for a context."""
        key = self._ctx(platform, channel, user)
        count = len(self._store.get(key, []))
        if key in self._store:
            del self._store[key]
        return count

    def compact(self) -> None:
        """Rewrite the on-disk JSONL to only the currently-retained items.

        The append-only persistence file grows unbounded over time even though
        the in-memory deques are capped at ``max_items_per_context``. Compaction
        atomically rewrites the file from the (capped) in-memory state, keeping
        the same one-JSON-object-per-line format that ``_load_from_disk`` reads.
        This is a no-op when persistence is disabled.
        """
        if not self._persist:
            return

        tmp_path = f"{self._path}.tmp"
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                for key, q in self._store.items():
                    for item in q:
                        f.write(
                            json.dumps(
                                {
                                    "key": key,
                                    "role": item.role,
                                    "content": item.content,
                                    "timestamp": item.timestamp,
                                }
                            )
                            + "\n"
                        )
            os.replace(tmp_path, self._path)
            self._appends_since_compact = 0
        except Exception as e:
            logger.warning("Failed to compact advisor memory at %s: %s", self._path, e)
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def flush(self) -> None:
        """Flush retained state to disk by compacting (no-op without persistence)."""
        self.compact()
