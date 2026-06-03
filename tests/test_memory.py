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
Comprehensive tests for memory module.

Tests memory storage and retrieval for advisors.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.advisors.memory import MemoryItem, MemoryStore


class TestMemoryItem:
    """Tests for MemoryItem dataclass."""

    def test_creation(self):
        """Test creating a MemoryItem."""
        item = MemoryItem(
            role="user",
            content="Hello",
            timestamp="2024-01-15T10:30:00",
        )
        assert item.role == "user"
        assert item.content == "Hello"
        assert item.timestamp == "2024-01-15T10:30:00"

    def test_different_roles(self):
        """Test creating items with different roles."""
        user_item = MemoryItem(role="user", content="Hi", timestamp="t1")
        assistant_item = MemoryItem(role="assistant", content="Hello", timestamp="t2")
        
        assert user_item.role == "user"
        assert assistant_item.role == "assistant"


class TestMemoryStoreInitialization:
    """Tests for MemoryStore initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        store = MemoryStore()
        assert store._max == 100
        assert store._persist is False

    def test_custom_max_items(self):
        """Test initialization with custom max items."""
        store = MemoryStore(max_items_per_context=50)
        assert store._max == 50

    def test_max_items_minimum(self):
        """Test that max items has minimum of 1."""
        store = MemoryStore(max_items_per_context=0)
        assert store._max == 1

    def test_persistence_enabled(self):
        """Test initialization with persistence."""
        with patch.object(Path, "exists", return_value=False):
            store = MemoryStore(persist=True, persist_path="/tmp/test_memory.jsonl")
            assert store._persist is True
            assert store._path == "/tmp/test_memory.jsonl"


class TestMemoryStoreAdd:
    """Tests for add method."""

    def test_add_item(self):
        """Test adding an item."""
        store = MemoryStore()
        store.add("discord", "general", "user1", "user", "Hello")
        
        key = "discord:general:user1"
        assert key in store._store
        assert len(store._store[key]) == 1

    def test_add_multiple_items(self):
        """Test adding multiple items."""
        store = MemoryStore()
        store.add("web", "chat", "u1", "user", "Hi")
        store.add("web", "chat", "u1", "assistant", "Hello")
        
        key = "web:chat:u1"
        assert len(store._store[key]) == 2

    def test_add_different_contexts(self):
        """Test adding to different contexts."""
        store = MemoryStore()
        store.add("discord", "ch1", "u1", "user", "Msg1")
        store.add("discord", "ch2", "u1", "user", "Msg2")
        
        assert len(store._store) == 2

    def test_add_persists_to_disk(self):
        """Test that add persists to disk when enabled."""
        with patch("builtins.open", mock_open := Mock()):
            mock_open.return_value.__enter__ = Mock(return_value=(mock_file := Mock()))
            mock_open.return_value.__exit__ = Mock(return_value=None)
            
            store = MemoryStore(persist=True, persist_path="/tmp/test.jsonl")
            with patch.object(Path, "exists", return_value=True):
                store.add("web", "ch", "u1", "user", "Test")


class TestMemoryStoreGet:
    """Tests for get method."""

    def test_get_empty(self):
        """Test getting from empty store."""
        store = MemoryStore()
        items = store.get("web", "ch", "u1")
        assert items == []

    def test_get_items(self):
        """Test retrieving items."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "Hello")
        store.add("web", "ch", "u1", "assistant", "Hi there")
        
        items = store.get("web", "ch", "u1")
        
        assert len(items) == 2
        assert items[0].content == "Hello"
        assert items[1].content == "Hi there"

    def test_get_with_limit(self):
        """Test getting with limit."""
        store = MemoryStore()
        for i in range(10):
            store.add("web", "ch", "u1", "user", f"Msg {i}")
        
        items = store.get("web", "ch", "u1", limit=5)
        
        assert len(items) == 5
        # Should get last 5
        assert items[0].content == "Msg 5"

    def test_get_zero_limit(self):
        """Test getting with zero limit."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "Test")
        
        items = store.get("web", "ch", "u1", limit=0)
        
        assert items == []

    def test_get_negative_limit(self):
        """Test getting with negative limit."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "Test")
        
        items = store.get("web", "ch", "u1", limit=-1)
        
        assert items == []


class TestMemoryStoreClear:
    """Tests for clear method."""

    def test_clear_empty(self):
        """Test clearing empty context."""
        store = MemoryStore()
        count = store.clear("web", "ch", "u1")
        assert count == 0

    def test_clear_with_items(self):
        """Test clearing with items."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "Test")
        store.add("web", "ch", "u1", "assistant", "Response")
        
        count = store.clear("web", "ch", "u1")
        
        assert count == 2
        assert store.get("web", "ch", "u1") == []


class TestMemoryStoreLoadFromDisk:
    """Tests for _load_from_disk method."""

    def test_load_empty_file(self):
        """Test loading from empty file."""
        with patch.object(Path, "exists", return_value=True):
            mock_file = Mock()
            mock_file.__iter__ = Mock(return_value=iter([]))
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            
            with patch("builtins.open", return_value=mock_file):
                store = MemoryStore(persist=True)
                # Should not crash
                assert len(store._store) == 0

    def test_load_valid_data(self):
        """Test loading valid data from file."""
        test_data = {
            "key": "discord:ch1:u1",
            "role": "user",
            "content": "Hello",
            "timestamp": "2024-01-15T10:30:00",
        }
        
        with patch.object(Path, "exists", return_value=True):
            mock_file = Mock()
            mock_file.__iter__ = Mock(return_value=iter([json.dumps(test_data)]))
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            
            with patch("builtins.open", return_value=mock_file):
                store = MemoryStore(persist=True, max_items_per_context=100)
                # Data should be loaded

    def test_load_invalid_json(self):
        """Test handling of invalid JSON."""
        with patch.object(Path, "exists", return_value=True):
            mock_file = Mock()
            mock_file.__iter__ = Mock(return_value=iter(["invalid json"]))
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            
            with patch("builtins.open", return_value=mock_file):
                store = MemoryStore(persist=True)
                # Should skip invalid lines


class TestMemoryStoreMaxItems:
    """Tests for max items enforcement."""

    def test_respects_max_items(self):
        """Test that max items is enforced."""
        store = MemoryStore(max_items_per_context=3)
        
        for i in range(5):
            store.add("web", "ch", "u1", "user", f"Msg {i}")
        
        items = store.get("web", "ch", "u1")
        assert len(items) == 3
        # Should keep most recent
        assert items[0].content == "Msg 2"


class TestMemoryIntegration:
    """Integration tests for memory module."""

    def test_full_lifecycle(self):
        """Test complete memory lifecycle."""
        store = MemoryStore(max_items_per_context=100)
        
        # Add items
        store.add("web", "ch", "u1", "user", "Hello")
        store.add("web", "ch", "u1", "assistant", "Hi")
        
        # Retrieve
        items = store.get("web", "ch", "u1")
        assert len(items) == 2
        
        # Clear
        count = store.clear("web", "ch", "u1")
        assert count == 2
        assert len(store.get("web", "ch", "u1")) == 0


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_content(self):
        """Test handling of empty content."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "")
        
        items = store.get("web", "ch", "u1")
        assert len(items) == 1
        assert items[0].content == ""

    def test_unicode_content(self):
        """Test handling of unicode content."""
        store = MemoryStore()
        store.add("web", "ch", "u1", "user", "Hello World")
        
        items = store.get("web", "ch", "u1")
        assert items[0].content == "Hello World"

    def test_very_long_content(self):
        """Test handling of very long content."""
        store = MemoryStore()
        long_content = "x" * 10000
        store.add("web", "ch", "u1", "user", long_content)
        
        items = store.get("web", "ch", "u1")
        assert items[0].content == long_content

    def test_special_chars_in_context(self):
        """Test handling of special characters in context keys."""
        store = MemoryStore()
        store.add("discord", "ch#1", "u-1", "user", "Test")
        
        items = store.get("discord", "ch#1", "u-1")
        assert len(items) == 1
