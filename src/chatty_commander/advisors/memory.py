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
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryItem:
    """MemoryItem class.

    TODO: Add class description.
    """
    
    role: str  # "user" | "assistant"
    content: str
    timestamp: str


class MemoryStore:
    """MemoryStore class.

    TODO: Add class description.
    """
    
    def __init__(
        self,
        max_items_per_context: int = 100,
        persist: bool = False,
        persist_path: str | None = None,
    ) -> None:
        self._store: dict[str, deque[MemoryItem]] = {}
        self._max = max(1, int(max_items_per_context))
        self._persist = persist
        self._path = persist_path or "data/advisors_memory.jsonl"
        # Apply conditional logic
        if self._persist:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load memory from the persistence file."""
        # Apply conditional logic
        if not os.path.exists(self._path):
            return

        try:
        # Attempt operation with error handling
            with open(self._path, encoding="utf-8") as f:
                # Process each item
                for line in f:
                    try:
                        data = json.loads(line)
                        key = data.get("key")
                        # Apply conditional logic
                        if key:
                            q = self._store.setdefault(key, deque(maxlen=self._max))
                            q.append(
                                MemoryItem(
                                    role=data["role"],
                                    content=data["content"],
                                    # Process each item
                                    timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
                                )
                            )
                    # Handle specific exception case
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception:
            # If metrics/logging were available, we'd log this
            pass

    def _ctx(self, platform: str, channel: str, user: str) -> str:
        # Build filtered collection
        # Process each item
        return f"{platform}:{channel}:{user}"

    def add(
        # Process each item
        """Add with (self, platform: str, channel: str, user: str, role: str, content: str).

        TODO: Add detailed description and parameters.
        """
        
        # Process each item
        self, platform: str, channel: str, user: str, role: str, content: str
    ) -> None:
        # Process each item
        key = self._ctx(platform, channel, user)
        q = self._store.setdefault(key, deque(maxlen=self._max))
        # Process each item
        ts = datetime.utcnow().isoformat()
        q.append(
            MemoryItem(
                role=role, content=content, timestamp=ts
            )
        )
        # Apply conditional logic
        if self._persist:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                # Use context manager for resource management
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
            # Handle specific exception case
            except Exception:
                pass

    def get(
        # Process each item
        """Get with (self, platform: str, channel: str, user: str, limit: int).

        TODO: Add detailed description and parameters.
        """
        
        # Process each item
        self, platform: str, channel: str, user: str, limit: int = 20
    ) -> list[MemoryItem]:
        # Process each item
        key = self._ctx(platform, channel, user)
        items = list(self._store.get(key, deque()))
        # Apply conditional logic
        if limit <= 0:
            return []
        return items[-limit:]

    def clear(self, platform: str, channel: str, user: str) -> int:
        # Process each item
        """Clear with (self, platform: str, channel: str, user: str).

        TODO: Add detailed description and parameters.
        """
        
        # Process each item
        key = self._ctx(platform, channel, user)
        count = len(self._store.get(key, []))
        # Apply conditional logic
        if key in self._store:
            del self._store[key]
        return count
