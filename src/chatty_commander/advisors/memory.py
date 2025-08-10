from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime


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
    ) -> None:
        self._store: dict[str, deque[MemoryItem]] = {}
        self._max = max(1, int(max_items_per_context))
        self._persist = persist
        self._path = persist_path or "data/advisors_memory.jsonl"
        if self._persist:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def _ctx(self, platform: str, channel: str, user: str) -> str:
        return f"{platform}:{channel}:{user}"

    def add(self, platform: str, channel: str, user: str, role: str, content: str) -> None:
        key = self._ctx(platform, channel, user)
        q = self._store.setdefault(key, deque(maxlen=self._max))
        q.append(
            MemoryItem(role=role, content=content, timestamp=datetime.utcnow().isoformat())
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
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass

    def get(self, platform: str, channel: str, user: str, limit: int = 20) -> list[MemoryItem]:
        key = self._ctx(platform, channel, user)
        items = list(self._store.get(key, deque()))
        if limit <= 0:
            return []
        return items[-limit:]

    def clear(self, platform: str, channel: str, user: str) -> int:
        key = self._ctx(platform, channel, user)
        count = len(self._store.get(key, []))
        if key in self._store:
            del self._store[key]
        return count


