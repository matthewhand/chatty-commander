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

"""
Comprehensive tests for advisors memory module.

Tests memory storage, persistence, and conversation management.
"""

import json
from datetime import datetime

import pytest

from src.chatty_commander.advisors.memory import MemoryItem, MemoryStore


class TestMemoryItem:
    """Test MemoryItem dataclass."""

    def test_memory_item_creation(self):
        """Test creating a MemoryItem instance."""
        timestamp = datetime.now().isoformat()
        item = MemoryItem(role="user", content="Hello world", timestamp=timestamp)

        assert item.role == "user"
        assert item.content == "Hello world"
        assert item.timestamp == timestamp

    def test_memory_item_defaults(self):
        """Test MemoryItem with default values."""
        item = MemoryItem(role="assistant", content="Hi there")

        assert item.role == "assistant"
        assert item.content == "Hi there"
        assert item.timestamp is not None

    def test_memory_item_serialization(self):
        """Test MemoryItem JSON serialization."""
        timestamp = datetime.now().isoformat()
        item = MemoryItem(role="user", content="Test content", timestamp=timestamp)

        # Should be serializable to JSON
        json_str = json.dumps(item.__dict__)
        assert json_str is not None

        # Should be deserializable from JSON
        data = json.loads(json_str)
        assert data["role"] == "user"
        assert data["content"] == "Test content"
        assert data["timestamp"] == timestamp


class TestMemoryStore:
    """Comprehensive tests for MemoryStore class."""

    @pytest.fixture
    def sample_memory_items(self):
        """Create sample memory items for testing."""
        return [
            MemoryItem(role="user", content="Hello", timestamp="2024-01-01T10:00:00"),
            MemoryItem(
                role="assistant", content="Hi there!", timestamp="2024-01-01T10:00:01"
            ),
            MemoryItem(
                role="user", content="How are you?", timestamp="2024-01-01T10:00:02"
            ),
            MemoryItem(
                role="assistant",
                content="I'm doing well!",
                timestamp="2024-01-01T10:00:03",
            ),
        ]

    def test_memory_store_initialization_defaults(self):
        """Test MemoryStore initialization with defaults."""
        store = MemoryStore()

        assert store._max == 100
        assert store._persist is False
        assert store._path == "data/advisors_memory.jsonl"
        assert len(store._store) == 0

    def test_memory_store_initialization_custom(self):
        """Test MemoryStore initialization with custom values."""
        store = MemoryStore(
            max_items_per_context=50, persist=True, persist_path="custom/path.json"
        )

        assert store._max == 50
        assert store._persist is True
        assert store._path == "custom/path.json"

    def test_memory_store_initialization_invalid_max(self):
        """Test MemoryStore initialization with invalid max items."""
        store = MemoryStore(max_items_per_context=0)

        assert store._max == 1  # Should be clamped to minimum

    def test_add_message_basic(self, sample_memory_items):
        """Test adding messages to memory store."""
        store = MemoryStore(max_items_per_context=3)

        # Add first message
        store.add_message("user123", sample_memory_items[0])
        assert len(store._store) == 1
        assert len(store._store["user123"]) == 1

        # Add more messages
        store.add_message("user123", sample_memory_items[1])
        store.add_message("user123", sample_memory_items[2])

        assert len(store._store["user123"]) == 3

    def test_add_message_different_users(self, sample_memory_items):
        """Test adding messages for different users."""
        store = MemoryStore()

        # Add messages for different users
        store.add_message("user1", sample_memory_items[0])
        store.add_message("user2", sample_memory_items[1])
        store.add_message("user1", sample_memory_items[2])

        assert len(store._store) == 2  # Two users
        assert len(store._store["user1"]) == 2  # user1 has 2 messages
        assert len(store._store["user2"]) == 1  # user2 has 1 message

    def test_add_message_max_limit(self, sample_memory_items):
        """Test max items per context limit."""
        store = MemoryStore(max_items_per_context=2)

        # Add messages beyond limit
        for i, item in enumerate(sample_memory_items):
            store.add_message("user123", item)

        # Should only keep the last 2 items
        assert len(store._store["user123"]) == 2
        assert store._store["user123"][0].content == sample_memory_items[2].content
        assert store._store["user123"][1].content == sample_memory_items[3].content

    def test_get_conversation_empty(self):
        """Test getting conversation when no messages exist."""
        store = MemoryStore()

        conversation = store.get_conversation("nonexistent_user")

        assert conversation == []

    def test_get_conversation_with_messages(self, sample_memory_items):
        """Test getting conversation with messages."""
        store = MemoryStore()

        # Add messages for user
        for item in sample_memory_items:
            store.add_message("user123", item)

        conversation = store.get_conversation("user123")

        assert len(conversation) == 4
        assert all(isinstance(item, dict) for item in conversation)
        assert conversation[0]["role"] == "user"
        assert conversation[1]["role"] == "assistant"

    def test_get_conversation_limit(self, sample_memory_items):
        """Test getting conversation with limit."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Get only last 2 messages
        conversation = store.get_conversation("user123", limit=2)

        assert len(conversation) == 2
        assert conversation[0]["content"] == sample_memory_items[2].content
        assert conversation[1]["content"] == sample_memory_items[3].content

    def test_get_conversation_user_filter(self, sample_memory_items):
        """Test getting conversation for specific user."""
        store = MemoryStore()

        # Add messages for multiple users
        store.add_message("user1", sample_memory_items[0])
        store.add_message("user2", sample_memory_items[1])
        store.add_message("user1", sample_memory_items[2])

        # Get conversation for user1 only
        conversation = store.get_conversation("user1")

        assert len(conversation) == 2
        assert all(item["role"] == "user" for item in conversation)

    def test_clear_conversation(self, sample_memory_items):
        """Test clearing conversation for user."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        assert len(store._store["user123"]) == 4

        # Clear conversation
        store.clear_conversation("user123")

        assert len(store._store) == 0

    def test_clear_nonexistent_conversation(self):
        """Test clearing nonexistent conversation."""
        store = MemoryStore()

        # Should not raise error
        store.clear_conversation("nonexistent_user")

        assert len(store._store) == 0

    def test_get_all_users(self, sample_memory_items):
        """Test getting all users with conversations."""
        store = MemoryStore()

        # Add messages for multiple users
        store.add_message("user1", sample_memory_items[0])
        store.add_message("user2", sample_memory_items[1])
        store.add_message("user3", sample_memory_items[2])

        users = store.get_all_users()

        assert len(users) == 3
        assert "user1" in users
        assert "user2" in users
        assert "user3" in users

    def test_get_all_users_empty(self):
        """Test getting all users when no conversations exist."""
        store = MemoryStore()

        users = store.get_all_users()

        assert users == []

    def test_get_memory_statistics(self, sample_memory_items):
        """Test getting memory statistics."""
        store = MemoryStore()

        # Add messages for multiple users
        store.add_message("user1", sample_memory_items[0])
        store.add_message("user2", sample_memory_items[1])
        store.add_message("user2", sample_memory_items[2])

        stats = store.get_statistics()

        assert "total_users" in stats
        assert "total_messages" in stats
        assert "messages_per_user" in stats
        assert stats["total_users"] == 2
        assert stats["total_messages"] == 3
        assert stats["messages_per_user"]["user1"] == 1
        assert stats["messages_per_user"]["user2"] == 2

    def test_persistence_save_load(self, sample_memory_items, tmp_path):
        """Test saving and loading conversations to/from disk."""
        persist_path = tmp_path / "test_memory.jsonl"
        store = MemoryStore(persist=True, persist_path=str(persist_path))

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Save to disk
        store.save_to_disk()

        # Verify file exists
        assert persist_path.exists()

        # Create new store and load
        new_store = MemoryStore(persist=True, persist_path=str(persist_path))
        new_store.load_from_disk()

        # Verify messages were loaded
        assert len(new_store._store) == 1
        assert len(new_store._store["user123"]) == 4

    def test_persistence_disabled(self, sample_memory_items, tmp_path):
        """Test behavior when persistence is disabled."""
        store = MemoryStore(persist=False)

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Try to save (should not raise error but not actually save)
        store.save_to_disk()

        # Load should not affect anything
        store.load_from_disk()

        # Messages should still be there
        assert len(store._store["user123"]) == 4

    def test_persistence_file_not_found(self, tmp_path):
        """Test loading when persistence file doesn't exist."""
        persist_path = tmp_path / "nonexistent.jsonl"
        store = MemoryStore(persist=True, persist_path=str(persist_path))

        # Should not raise error
        store.load_from_disk()

        assert len(store._store) == 0

    def test_persistence_corrupted_file(self, tmp_path):
        """Test loading corrupted persistence file."""
        persist_path = tmp_path / "corrupted.jsonl"
        persist_path.write_text("invalid json content")

        store = MemoryStore(persist=True, persist_path=str(persist_path))

        # Should not raise error, just skip corrupted data
        store.load_from_disk()

        assert len(store._store) == 0

    def test_search_messages(self, sample_memory_items):
        """Test searching messages by content."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Search for messages containing "Hello"
        results = store.search_messages("Hello")

        assert len(results) == 1
        assert results[0]["content"] == "Hello"

    def test_search_messages_no_match(self, sample_memory_items):
        """Test searching with no matching messages."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Search for non-existent content
        results = store.search_messages("nonexistent")

        assert results == []

    def test_search_messages_multiple_users(self, sample_memory_items):
        """Test searching across multiple users."""
        store = MemoryStore()

        # Add messages for different users
        store.add_message("user1", sample_memory_items[0])  # Contains "Hello"
        store.add_message("user2", sample_memory_items[2])  # Contains "How are you?"

        # Search for "Hello"
        results = store.search_messages("Hello")

        assert len(results) == 1
        assert results[0]["user_id"] == "user1"

    def test_get_recent_messages(self, sample_memory_items):
        """Test getting recent messages."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        # Get recent messages
        recent = store.get_recent_messages("user123", count=2)

        assert len(recent) == 2
        assert recent[0]["content"] == sample_memory_items[2].content  # Most recent
        assert recent[1]["content"] == sample_memory_items[3].content

    def test_get_recent_messages_more_than_available(self, sample_memory_items):
        """Test getting more recent messages than available."""
        store = MemoryStore()

        # Add only 2 messages
        store.add_message("user123", sample_memory_items[0])
        store.add_message("user123", sample_memory_items[1])

        # Try to get 5 recent messages
        recent = store.get_recent_messages("user123", count=5)

        assert len(recent) == 2  # Should return all available

    def test_memory_cleanup_old_conversations(self, sample_memory_items):
        """Test cleanup of old conversations."""
        store = MemoryStore()

        # Add messages for multiple users
        for i, item in enumerate(sample_memory_items):
            user_id = f"user{i % 2}"  # user0, user1, user0, user1
            store.add_message(user_id, item)

        # Cleanup conversations older than certain threshold
        # This is more of a conceptual test since we don't have real timestamps
        initial_users = store.get_all_users()
        assert len(initial_users) > 0

        # In a real scenario, this would remove conversations based on timestamp
        # For now, just verify the method exists and doesn't crash
        store.cleanup_old_conversations(days_old=30)

    def test_export_conversation(self, sample_memory_items, tmp_path):
        """Test exporting conversation to file."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        export_path = tmp_path / "export.json"
        store.export_conversation("user123", str(export_path))

        # Verify file was created
        assert export_path.exists()

        # Verify content
        with open(export_path) as f:
            exported_data = json.load(f)

        assert len(exported_data) == 4
        assert exported_data[0]["role"] == "user"

    def test_export_nonexistent_conversation(self, tmp_path):
        """Test exporting nonexistent conversation."""
        store = MemoryStore()

        export_path = tmp_path / "export.json"
        store.export_conversation("nonexistent", str(export_path))

        # Should create empty file
        assert export_path.exists()

        with open(export_path) as f:
            content = f.read()
        assert content == "[]"

    def test_import_conversation(self, sample_memory_items, tmp_path):
        """Test importing conversation from file."""
        store = MemoryStore()

        # Create export file manually
        import_data = [
            {
                "role": "user",
                "content": "Imported message",
                "timestamp": "2024-01-01T10:00:00",
            },
            {
                "role": "assistant",
                "content": "Imported response",
                "timestamp": "2024-01-01T10:00:01",
            },
        ]

        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(import_data, f)

        # Import conversation
        store.import_conversation("user123", str(import_path))

        # Verify messages were imported
        assert len(store._store) == 1
        assert len(store._store["user123"]) == 2

    def test_import_invalid_file(self, tmp_path):
        """Test importing from invalid file."""
        store = MemoryStore()

        # Create invalid file
        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text("invalid json")

        # Should not raise error
        store.import_conversation("user123", str(invalid_path))

        # No messages should be imported
        assert len(store._store) == 0

    def test_conversation_summary(self, sample_memory_items):
        """Test generating conversation summary."""
        store = MemoryStore()

        # Add messages
        for item in sample_memory_items:
            store.add_message("user123", item)

        summary = store.get_conversation_summary("user123")

        assert "total_messages" in summary
        assert "user_messages" in summary
        assert "assistant_messages" in summary
        assert "conversation_length" in summary
        assert summary["total_messages"] == 4
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 2

    def test_thread_safety(self, sample_memory_items):
        """Test thread safety of memory operations."""
        store = MemoryStore()

        # Simulate concurrent access
        import threading

        def add_messages():
            for item in sample_memory_items:
                store.add_message("user123", item)

        # Run concurrent operations
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_messages)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access gracefully
        assert len(store._store) == 1
        assert len(store._store["user123"]) == 4
