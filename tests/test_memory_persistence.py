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

import json
import os
import tempfile

from chatty_commander.advisors.memory import MemoryStore


def test_memory_persistence_roundtrip():
    """Test that memory is persisted to disk and loaded back."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        clean_path = tmp.name

    try:
        # 1. Create store and add items
        store1 = MemoryStore(persist=True, persist_path=clean_path)
        store1.add("discord", "gen", "u1", "user", "Hello")
        store1.add("discord", "gen", "u1", "assistant", "Hi there")

        # Verify file content
        with open(clean_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            data = json.loads(lines[0])
            assert data["content"] == "Hello"
            assert data["role"] == "user"

        # 2. Create new store (simulation restart)
        store2 = MemoryStore(persist=True, persist_path=clean_path)

        # Verify encoded data loaded
        items = store2.get("discord", "gen", "u1")
        assert len(items) == 2
        assert items[0].content == "Hello"
        assert items[0].role == "user"
        assert items[1].content == "Hi there"
        assert items[1].role == "assistant"

        # Verify timestamp preserved
        assert items[0].timestamp == data["timestamp"]

    finally:
        if os.path.exists(clean_path):
            os.remove(clean_path)

def test_memory_persistence_bad_data():
    """Test resilience against corrupted data."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as tmp:
        clean_path = tmp.name
        tmp.write('{"valid": "json", "but": "wrong schema"}\n')
        tmp.write('corrupted { json\n')
        tmp.write(json.dumps({
            "key": "discord:gen:u1",
            "role": "user",
            "content": "survivor",
            "timestamp": "2024-01-01"
        }) + "\n")

    try:
        store = MemoryStore(persist=True, persist_path=clean_path)
        items = store.get("discord", "gen", "u1")

        # Should populate the one valid item and ignore others
        assert len(items) == 1
        assert items[0].content == "survivor"

    finally:
        if os.path.exists(clean_path):
            os.remove(clean_path)
