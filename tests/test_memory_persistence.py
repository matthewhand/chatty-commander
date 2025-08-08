import os
import tempfile

from chatty_commander.advisors.memory import MemoryStore


def test_memory_store_persistence_appends_lines():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "mem.jsonl")
        store = MemoryStore(max_items_per_context=10, persist=True, persist_path=path)
        store.add("discord", "c1", "u1", "user", "hello")
        store.add("discord", "c1", "u1", "assistant", "hi")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert "\"content\": \"hello\"" in lines[0]

