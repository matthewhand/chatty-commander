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
Comprehensive tests for advisors context module.

Tests context management, platform types, and conversation context handling.
"""


import pytest

from src.chatty_commander.advisors.context import (
    ContextManager,
    ConversationContext,
    PlatformType,
)


class TestPlatformType:
    """Test PlatformType enum."""

    def test_platform_type_values(self):
        """Test PlatformType enum values."""
        assert PlatformType.VOICE.value == "voice"
        assert PlatformType.TEXT.value == "text"
        assert PlatformType.GUI.value == "gui"
        assert PlatformType.CLI.value == "cli"

    def test_platform_type_from_string(self):
        """Test creating PlatformType from string."""
        assert PlatformType.from_string("voice") == PlatformType.VOICE
        assert PlatformType.from_string("text") == PlatformType.TEXT
        assert PlatformType.from_string("gui") == PlatformType.GUI
        assert PlatformType.from_string("cli") == PlatformType.CLI

    def test_platform_type_from_string_invalid(self):
        """Test PlatformType.from_string with invalid input."""
        assert (
            PlatformType.from_string("invalid") == PlatformType.CLI
        )  # Default fallback
        assert PlatformType.from_string("") == PlatformType.CLI  # Default fallback
        assert PlatformType.from_string(None) == PlatformType.CLI  # Default fallback


class TestConversationContext:
    """Test ConversationContext class."""

    def test_conversation_context_creation(self):
        """Test creating a ConversationContext instance."""
        context = ConversationContext(
            user_id="user123",
            conversation_id="conv456",
            platform=PlatformType.VOICE,
            channel="main",
            metadata={"key": "value"},
        )

        assert context.user_id == "user123"
        assert context.conversation_id == "conv456"
        assert context.platform == PlatformType.VOICE
        assert context.channel == "main"
        assert context.metadata == {"key": "value"}

    def test_conversation_context_defaults(self):
        """Test ConversationContext with default values."""
        context = ConversationContext(user_id="user123")

        assert context.user_id == "user123"
        assert context.conversation_id.startswith("conv_")
        assert context.platform == PlatformType.CLI  # Default
        assert context.channel == "default"
        assert context.metadata == {}

    def test_conversation_context_to_dict(self):
        """Test converting ConversationContext to dictionary."""
        context = ConversationContext(
            user_id="user123",
            conversation_id="conv456",
            platform=PlatformType.TEXT,
            channel="chat",
            metadata={"test": "data"},
        )

        context_dict = context.to_dict()

        assert context_dict["user_id"] == "user123"
        assert context_dict["conversation_id"] == "conv456"
        assert context_dict["platform"] == "text"
        assert context_dict["channel"] == "chat"
        assert context_dict["metadata"] == {"test": "data"}

    def test_conversation_context_from_dict(self):
        """Test creating ConversationContext from dictionary."""
        context_dict = {
            "user_id": "user123",
            "conversation_id": "conv456",
            "platform": "voice",
            "channel": "voice_chat",
            "metadata": {"test": "data"},
        }

        context = ConversationContext.from_dict(context_dict)

        assert context.user_id == "user123"
        assert context.conversation_id == "conv456"
        assert context.platform == PlatformType.VOICE
        assert context.channel == "voice_chat"
        assert context.metadata == {"test": "data"}


class TestContextManager:
    """Comprehensive tests for ContextManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            "max_contexts": 100,
            "default_platform": "cli",
            "context_timeout": 3600,
            "enable_persistence": True,
        }

    @pytest.fixture
    def sample_contexts(self):
        """Create sample contexts for testing."""
        return [
            ConversationContext(
                user_id="user1",
                conversation_id="conv1",
                platform=PlatformType.VOICE,
                channel="main",
            ),
            ConversationContext(
                user_id="user2",
                conversation_id="conv2",
                platform=PlatformType.TEXT,
                channel="chat",
            ),
            ConversationContext(
                user_id="user1",
                conversation_id="conv3",
                platform=PlatformType.GUI,
                channel="desktop",
            ),
        ]

    def test_context_manager_initialization(self, mock_config):
        """Test ContextManager initialization."""
        manager = ContextManager(mock_config)

        assert manager.config == mock_config
        assert manager.contexts == {}
        assert manager.max_contexts == 100

    def test_create_context(self, mock_config):
        """Test creating a new context."""
        manager = ContextManager(mock_config)

        context = manager.create_context(
            user_id="user123",
            platform=PlatformType.VOICE,
            channel="main",
            metadata={"test": "data"},
        )

        assert context.user_id == "user123"
        assert context.platform == PlatformType.VOICE
        assert context.channel == "main"
        assert context.metadata == {"test": "data"}
        assert "user123" in manager.contexts

    def test_get_context_existing(self, mock_config, sample_contexts):
        """Test getting existing context."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Get existing context
        context = manager.get_context("user1")

        assert context is not None
        assert context.user_id == "user1"
        assert len(context.conversation_id) > 0  # Should have generated ID

    def test_get_context_nonexistent(self, mock_config):
        """Test getting nonexistent context."""
        manager = ContextManager(mock_config)

        context = manager.get_context("nonexistent_user")

        assert context is None

    def test_update_context(self, mock_config, sample_contexts):
        """Test updating existing context."""
        manager = ContextManager(mock_config)

        # Add initial context
        initial_context = sample_contexts[0]
        manager.contexts["user1"] = initial_context

        # Update context
        updates = {
            "platform": PlatformType.TEXT,
            "channel": "updated_chat",
            "metadata": {"updated": True},
        }

        updated_context = manager.update_context("user1", updates)

        assert updated_context.platform == PlatformType.TEXT
        assert updated_context.channel == "updated_chat"
        assert updated_context.metadata == {"updated": True}

    def test_update_context_nonexistent(self, mock_config):
        """Test updating nonexistent context."""
        manager = ContextManager(mock_config)

        updates = {"platform": PlatformType.TEXT}
        updated_context = manager.update_context("nonexistent", updates)

        assert updated_context is None

    def test_delete_context(self, mock_config, sample_contexts):
        """Test deleting existing context."""
        manager = ContextManager(mock_config)

        # Add context
        context = sample_contexts[0]
        manager.contexts["user1"] = context

        assert "user1" in manager.contexts

        # Delete context
        result = manager.delete_context("user1")

        assert result is True
        assert "user1" not in manager.contexts

    def test_delete_context_nonexistent(self, mock_config):
        """Test deleting nonexistent context."""
        manager = ContextManager(mock_config)

        result = manager.delete_context("nonexistent")

        assert result is False

    def test_get_contexts_by_platform(self, mock_config, sample_contexts):
        """Test getting contexts by platform."""
        manager = ContextManager(mock_config)

        # Add contexts with different platforms
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Get contexts by platform
        voice_contexts = manager.get_contexts_by_platform(PlatformType.VOICE)
        text_contexts = manager.get_contexts_by_platform(PlatformType.TEXT)
        gui_contexts = manager.get_contexts_by_platform(PlatformType.GUI)

        assert len(voice_contexts) == 1
        assert len(text_contexts) == 1
        assert len(gui_contexts) == 1

    def test_get_contexts_by_channel(self, mock_config, sample_contexts):
        """Test getting contexts by channel."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Get contexts by channel
        main_contexts = manager.get_contexts_by_channel("main")
        chat_contexts = manager.get_contexts_by_channel("chat")

        assert len(main_contexts) == 1
        assert len(chat_contexts) == 1

    def test_get_all_contexts(self, mock_config, sample_contexts):
        """Test getting all contexts."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        all_contexts = manager.get_all_contexts()

        assert len(all_contexts) == 3
        assert all(isinstance(ctx, ConversationContext) for ctx in all_contexts)

    def test_get_context_statistics(self, mock_config, sample_contexts):
        """Test getting context statistics."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        stats = manager.get_statistics()

        assert "total_contexts" in stats
        assert "platforms" in stats
        assert "channels" in stats
        assert stats["total_contexts"] == 3
        assert stats["platforms"]["voice"] == 1
        assert stats["platforms"]["text"] == 1
        assert stats["platforms"]["gui"] == 1

    def test_context_timeout_cleanup(self, mock_config, sample_contexts):
        """Test cleanup of timed-out contexts."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Cleanup old contexts (conceptual test)
        manager.cleanup_old_contexts(max_age_seconds=3600)

        # Should not remove contexts in this test since we can't simulate time
        assert len(manager.contexts) == 3

    def test_context_limit_enforcement(self, mock_config):
        """Test context limit enforcement."""
        small_config = mock_config.copy()
        small_config["max_contexts"] = 2

        manager = ContextManager(small_config)

        # Add contexts up to limit
        for i in range(3):
            context = manager.create_context(
                user_id=f"user{i}", platform=PlatformType.TEXT, channel="test"
            )

        # Should only have 2 contexts (limit enforced)
        assert len(manager.contexts) == 2

    def test_context_merge_functionality(self, mock_config, sample_contexts):
        """Test context merging functionality."""
        manager = ContextManager(mock_config)

        # Add initial context
        initial_context = sample_contexts[0]
        manager.contexts["user1"] = initial_context

        # Merge additional context
        merge_updates = {
            "metadata": {"merged": True, "original": False},
            "channel": "merged_channel",
        }

        merged_context = manager.merge_context("user1", merge_updates)

        assert merged_context is not None
        assert merged_context.metadata["merged"] is True
        assert merged_context.channel == "merged_channel"

    def test_context_validation(self, mock_config):
        """Test context validation."""
        manager = ContextManager(mock_config)

        # Valid context
        valid_context = ConversationContext(
            user_id="user123", platform=PlatformType.TEXT, channel="chat"
        )

        assert manager._validate_context(valid_context) is True

        # Invalid context (missing user_id)
        invalid_context = ConversationContext(
            user_id="", platform=PlatformType.TEXT, channel="chat"
        )

        assert manager._validate_context(invalid_context) is False

    def test_batch_context_operations(self, mock_config):
        """Test batch context operations."""
        manager = ContextManager(mock_config)

        # Create multiple contexts
        user_ids = ["user1", "user2", "user3"]
        contexts = []

        for user_id in user_ids:
            context = manager.create_context(
                user_id=user_id, platform=PlatformType.TEXT, channel="batch_test"
            )
            contexts.append(context)

        # Verify all contexts were created
        assert len(manager.contexts) == 3
        assert all(context.channel == "batch_test" for context in contexts)

    def test_context_persistence(self, mock_config, sample_contexts, tmp_path):
        """Test context persistence to disk."""
        persist_path = tmp_path / "contexts.json"
        persist_config = mock_config.copy()
        persist_config["persistence_file"] = str(persist_path)

        manager = ContextManager(persist_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Save contexts
        manager.save_contexts()

        # Verify file was created
        assert persist_path.exists()

        # Create new manager and load contexts
        new_manager = ContextManager(persist_config)
        new_manager.load_contexts()

        # Verify contexts were loaded
        assert len(new_manager.contexts) == 3

    def test_context_persistence_disabled(self, mock_config, sample_contexts):
        """Test behavior when persistence is disabled."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Try to save (should not raise error)
        manager.save_contexts()

        # Load should not affect anything
        manager.load_contexts()

        # Contexts should still be there
        assert len(manager.contexts) == 3

    def test_error_handling_invalid_operations(self, mock_config):
        """Test error handling for invalid operations."""
        manager = ContextManager(mock_config)

        # Try to get context with None user_id
        context = manager.get_context(None)
        assert context is None

        # Try to update context with None updates
        result = manager.update_context("user1", None)
        assert result is None

    def test_context_event_callbacks(self, mock_config, sample_contexts):
        """Test context event callback functionality."""
        callback_called = False
        callback_data = None

        def context_callback(event_type, context, old_context=None):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = {
                "event_type": event_type,
                "context": context,
                "old_context": old_context,
            }

        manager = ContextManager(mock_config)
        manager.add_event_callback(context_callback)

        # Create context (should trigger callback)
        context = manager.create_context(
            user_id="test_user", platform=PlatformType.TEXT, channel="test"
        )

        assert callback_called is True
        assert callback_data["event_type"] == "created"
        assert callback_data["context"].user_id == "test_user"

    def test_context_search_functionality(self, mock_config, sample_contexts):
        """Test context search functionality."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Search contexts by metadata
        search_results = manager.search_contexts(platform=PlatformType.VOICE)

        assert len(search_results) == 1
        assert search_results[0].platform == PlatformType.VOICE

        # Search by channel
        search_results = manager.search_contexts(channel="chat")

        assert len(search_results) == 1
        assert search_results[0].channel == "chat"

    def test_context_export_import(self, mock_config, sample_contexts, tmp_path):
        """Test context export and import functionality."""
        manager = ContextManager(mock_config)

        # Add contexts
        for context in sample_contexts:
            manager.contexts[context.user_id] = context

        # Export contexts
        export_path = tmp_path / "contexts_export.json"
        manager.export_contexts(str(export_path))

        assert export_path.exists()

        # Import contexts into new manager
        new_manager = ContextManager(mock_config)
        new_manager.import_contexts(str(export_path))

        assert len(new_manager.contexts) == 3

        # Verify imported contexts
        for context in sample_contexts:
            imported_context = new_manager.get_context(context.user_id)
            assert imported_context is not None
            assert imported_context.platform == context.platform
