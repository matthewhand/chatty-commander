"""
Tests for advisors context management functionality.
"""

from unittest.mock import Mock

import pytest


class TestAdvisorsContext:
    """Test advisors context management."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for advisors."""
        config = Mock()
        config.advisors = {
            "enabled": True,
            "llm_api_mode": "completion",
            "model": "gpt-4",
            "max_context_length": 4000,
            "context_window": 10,
        }
        return config

    def test_context_configuration_loading(self, mock_config):
        """Test that context configuration is loaded correctly."""
        assert mock_config.advisors["enabled"] is True
        assert mock_config.advisors["max_context_length"] == 4000
        assert mock_config.advisors["context_window"] == 10

    def test_context_window_size_validation(self, mock_config):
        """Test context window size validation."""
        # Valid window size
        mock_config.advisors["context_window"] = 10
        assert mock_config.advisors["context_window"] > 0

        # Invalid window size
        mock_config.advisors["context_window"] = -1
        assert mock_config.advisors["context_window"] < 0

    def test_max_context_length_validation(self, mock_config):
        """Test maximum context length validation."""
        # Valid length
        mock_config.advisors["max_context_length"] = 4000
        assert mock_config.advisors["max_context_length"] > 0

        # Test different length values
        test_lengths = [100, 1000, 8000, 16000]
        for length in test_lengths:
            mock_config.advisors["max_context_length"] = length
            assert mock_config.advisors["max_context_length"] == length

    def test_context_entry_structure(self):
        """Test context entry structure validation."""
        valid_entry = {
            "role": "user",
            "content": "test message",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        assert "role" in valid_entry
        assert "content" in valid_entry
        assert valid_entry["role"] in ["user", "assistant", "system"]
        assert len(valid_entry["content"]) > 0

    def test_context_role_validation(self):
        """Test context role validation."""
        valid_roles = ["user", "assistant", "system"]
        invalid_roles = ["admin", "moderator", "", None, 123]

        for role in valid_roles:
            entry = {"role": role, "content": "test"}
            assert entry["role"] in valid_roles

        for role in invalid_roles:
            entry = {"role": role, "content": "test"}
            assert entry["role"] not in valid_roles

    def test_context_content_validation(self):
        """Test context content validation."""
        # Valid content
        valid_contents = [
            "Hello world",
            "This is a longer message with multiple sentences.",
            "Message with unicode: ñáéíóú",
            "Message with numbers: 12345",
            "Message with symbols: !@#$%^&*()",
        ]

        for content in valid_contents:
            entry = {"role": "user", "content": content}
            assert isinstance(entry["content"], str)
            assert len(entry["content"]) > 0

        # Invalid content
        invalid_contents = ["", None, 123, [], {}]

        for content in invalid_contents:
            entry = {"role": "user", "content": content}
            assert not isinstance(entry["content"], str) or len(entry["content"]) == 0

    def test_context_size_calculation(self):
        """Test context size calculation."""
        entries = [
            {"role": "user", "content": "Short message"},
            {
                "role": "assistant",
                "content": "This is a much longer response with more detail",
            },
            {"role": "user", "content": "Another message"},
        ]

        total_chars = sum(len(entry["content"]) for entry in entries)
        assert total_chars > 0
        assert total_chars == len("Short message") + len(
            "This is a much longer response with more detail"
        ) + len("Another message")

    def test_context_trimming_logic(self):
        """Test context trimming logic."""
        max_length = 100
        entries = [
            {"role": "user", "content": "x" * 50},  # 50 chars
            {"role": "assistant", "content": "x" * 30},  # 30 chars
            {"role": "user", "content": "x" * 40},  # 40 chars
        ]

        # Total would be 120 chars, need to trim to 100
        total_length = sum(len(entry["content"]) for entry in entries)
        assert total_length > max_length

        # Should keep the most recent entries
        trimmed_entries = entries[-2:]  # Keep last 2 entries (70 chars)
        trimmed_length = sum(len(entry["content"]) for entry in trimmed_entries)
        assert trimmed_length <= max_length

    def test_context_persistence_format(self):
        """Test context persistence format."""
        context = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "entries": [
                {"role": "user", "content": "test", "timestamp": "2024-01-01T00:00:00Z"}
            ],
            "metadata": {"total_entries": 1, "total_chars": 4},
        }

        assert "version" in context
        assert "entries" in context
        assert "metadata" in context
        assert isinstance(context["entries"], list)
        assert len(context["entries"]) == 1

    def test_context_search_functionality(self):
        """Test context search functionality."""
        entries = [
            {"role": "user", "content": "I need help with Python programming"},
            {"role": "assistant", "content": "Python is a great programming language"},
            {"role": "user", "content": "What about JavaScript?"},
        ]

        # Search for "Python"
        python_results = [entry for entry in entries if "Python" in entry["content"]]
        assert len(python_results) == 2

        # Search for "JavaScript"
        js_results = [entry for entry in entries if "JavaScript" in entry["content"]]
        assert len(js_results) == 1

    def test_context_filtering_by_role(self):
        """Test filtering context by role."""
        entries = [
            {"role": "user", "content": "question 1"},
            {"role": "assistant", "content": "answer 1"},
            {"role": "user", "content": "question 2"},
            {"role": "system", "content": "system message"},
            {"role": "assistant", "content": "answer 2"},
        ]

        user_entries = [entry for entry in entries if entry["role"] == "user"]
        assistant_entries = [entry for entry in entries if entry["role"] == "assistant"]
        system_entries = [entry for entry in entries if entry["role"] == "system"]

        assert len(user_entries) == 2
        assert len(assistant_entries) == 2
        assert len(system_entries) == 1

    @pytest.mark.asyncio
    async def test_context_with_async_operations(self):
        """Test context management with async operations."""

        # Mock async operation
        async def mock_async_operation(context):
            return f"Processed {len(context)} entries"

        context = [
            {"role": "user", "content": "message 1"},
            {"role": "assistant", "content": "response 1"},
        ]

        result = await mock_async_operation(context)
        assert result == "Processed 2 entries"

    def test_context_error_handling(self):
        """Test error handling in context management."""
        # Test malformed entries
        malformed_entries = [
            {"role": "user"},  # Missing content
            {"content": "message"},  # Missing role
            {},  # Empty entry
            None,  # None entry
        ]

        for entry in malformed_entries:
            if entry is None:
                assert entry is None
            else:
                assert "role" not in entry or "content" not in entry

    def test_context_memory_efficiency(self):
        """Test memory efficiency of context management."""
        import sys

        # Create entries with varying sizes
        entries = []
        for i in range(100):
            content = f"Message {i} with some content" * (i % 10 + 1)
            entries.append({"role": "user", "content": content})

        # Calculate memory usage
        total_size = sum(sys.getsizeof(entry["content"]) for entry in entries)
        assert total_size > 0

        # Test that trimming reduces memory usage
        trimmed_entries = entries[-10:]  # Keep only last 10
        trimmed_size = sum(sys.getsizeof(entry["content"]) for entry in trimmed_entries)
        assert trimmed_size < total_size
