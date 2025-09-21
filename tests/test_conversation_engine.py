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
Comprehensive tests for conversation engine module.

Tests conversation context management, sentiment analysis, persona-based responses,
and conversation memory persistence.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.advisors.conversation_engine import (
    ConversationContext,
    ConversationEngine,
    ConversationTurn,
)


class TestConversationTurn:
    """Test ConversationTurn dataclass."""

    def test_conversation_turn_creation(self):
        """Test creating a ConversationTurn instance."""
        timestamp = datetime.now()
        turn = ConversationTurn(
            timestamp=timestamp,
            user_input="Hello",
            assistant_response="Hi there!",
            context={"user_id": "user123"},
            sentiment="positive",
            intent="greeting",
        )

        assert turn.timestamp == timestamp
        assert turn.user_input == "Hello"
        assert turn.assistant_response == "Hi there!"
        assert turn.context == {"user_id": "user123"}
        assert turn.sentiment == "positive"
        assert turn.intent == "greeting"

    def test_conversation_turn_optional_fields(self):
        """Test ConversationTurn with optional fields omitted."""
        timestamp = datetime.now()
        turn = ConversationTurn(
            timestamp=timestamp,
            user_input="How are you?",
            assistant_response="I'm doing well!",
            context={},
        )

        assert turn.sentiment is None
        assert turn.intent is None


class TestConversationContext:
    """Test ConversationContext class."""

    def test_conversation_context_creation(self):
        """Test creating a ConversationContext instance."""
        context = ConversationContext(
            user_id="user123",
            conversation_id="conv456",
            persona="assistant",
            preferences={"language": "en"},
        )

        assert context.user_id == "user123"
        assert context.conversation_id == "conv456"
        assert context.persona == "assistant"
        assert context.preferences == {"language": "en"}

    def test_conversation_context_defaults(self):
        """Test ConversationContext with default values."""
        context = ConversationContext(user_id="user123")

        assert context.conversation_id.startswith("conv_")
        assert context.persona == "default"
        assert context.preferences == {}


class TestConversationEngine:
    """Comprehensive tests for ConversationEngine class."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        provider = Mock()
        provider.generate_response.return_value = "This is a test response"
        return provider

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "default_persona": "assistant",
            "max_context_length": 1000,
            "sentiment_analysis_enabled": True,
            "intent_classification_enabled": True,
        }

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for conversation storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_conversation_engine_initialization(self, sample_config):
        """Test ConversationEngine initialization."""
        engine = ConversationEngine(sample_config)

        assert engine.config == sample_config
        assert engine.conversations == {}
        assert engine.default_persona == "assistant"

    @patch(
        "src.chatty_commander.advisors.conversation_engine.ConversationEngine._analyze_sentiment"
    )
    @patch(
        "src.chatty_commander.advisors.conversation_engine.ConversationEngine._classify_intent"
    )
    def test_process_conversation_basic(
        self,
        mock_classify_intent,
        mock_analyze_sentiment,
        mock_llm_provider,
        sample_config,
    ):
        """Test basic conversation processing."""
        mock_analyze_sentiment.return_value = "positive"
        mock_classify_intent.return_value = "question"

        engine = ConversationEngine(sample_config)
        engine.llm_provider = mock_llm_provider

        result = engine.process_conversation(
            user_id="user123",
            user_input="What is the weather like?",
            context={"location": "San Francisco"},
        )

        assert "response" in result
        assert "sentiment" in result
        assert "intent" in result
        assert result["sentiment"] == "positive"
        assert result["intent"] == "question"

    def test_conversation_context_persistence(self, sample_config, temp_storage_dir):
        """Test conversation context persistence to disk."""
        storage_path = temp_storage_dir / "conversations.json"
        sample_config["storage_path"] = str(storage_path)

        engine = ConversationEngine(sample_config)

        # Add a conversation
        engine.conversations["user123"] = {
            "turns": [
                ConversationTurn(
                    timestamp=datetime.now(),
                    user_input="Hello",
                    assistant_response="Hi there!",
                    context={"user_id": "user123"},
                )
            ]
        }

        # Save conversations
        engine.save_conversations()

        # Verify file was created
        assert storage_path.exists()

        # Load conversations
        new_engine = ConversationEngine(sample_config)
        new_engine.load_conversations()

        assert "user123" in new_engine.conversations

    def test_conversation_history_management(self, sample_config):
        """Test conversation history management and limits."""
        sample_config["max_turns_per_conversation"] = 5

        engine = ConversationEngine(sample_config)

        # Add multiple turns
        for i in range(7):
            turn = ConversationTurn(
                timestamp=datetime.now(),
                user_input=f"Message {i}",
                assistant_response=f"Response {i}",
                context={"user_id": "user123"},
            )
            engine.add_conversation_turn("user123", turn)

        # Check that only the last 5 turns are kept
        assert len(engine.conversations["user123"]["turns"]) == 5
        assert engine.conversations["user123"]["turns"][0].user_input == "Message 2"

    def test_persona_switching(self, sample_config):
        """Test persona switching functionality."""
        engine = ConversationEngine(sample_config)

        # Test switching to different persona
        result = engine.switch_persona("user123", "expert")

        assert result["persona"] == "expert"
        assert engine.conversations["user123"]["context"]["persona"] == "expert"

    @patch(
        "src.chatty_commander.advisors.conversation_engine.ConversationEngine._analyze_sentiment"
    )
    def test_sentiment_analysis_integration(
        self, mock_analyze_sentiment, sample_config
    ):
        """Test sentiment analysis integration."""
        mock_analyze_sentiment.return_value = "negative"

        engine = ConversationEngine(sample_config)

        result = engine.analyze_sentiment("I hate this!")

        assert result == "negative"
        mock_analyze_sentiment.assert_called_once_with("I hate this!")

    @patch(
        "src.chatty_commander.advisors.conversation_engine.ConversationEngine._classify_intent"
    )
    def test_intent_classification_integration(
        self, mock_classify_intent, sample_config
    ):
        """Test intent classification integration."""
        mock_classify_intent.return_value = "command"

        engine = ConversationEngine(sample_config)

        result = engine.classify_intent("Turn on the lights")

        assert result == "command"
        mock_classify_intent.assert_called_once_with("Turn on the lights")

    def test_conversation_statistics(self, sample_config):
        """Test conversation statistics generation."""
        engine = ConversationEngine(sample_config)

        # Add some test data
        for i in range(3):
            turn = ConversationTurn(
                timestamp=datetime.now(),
                user_input=f"Test message {i}",
                assistant_response=f"Test response {i}",
                context={"user_id": "user123"},
                sentiment="positive" if i % 2 == 0 else "neutral",
                intent="question" if i % 2 == 0 else "statement",
            )
            engine.add_conversation_turn("user123", turn)

        stats = engine.get_conversation_statistics("user123")

        assert "total_turns" in stats
        assert "sentiment_distribution" in stats
        assert "intent_distribution" in stats
        assert stats["total_turns"] == 3

    def test_error_handling_invalid_user(self, sample_config):
        """Test error handling for invalid user operations."""
        engine = ConversationEngine(sample_config)

        # Try to get statistics for non-existent user
        stats = engine.get_conversation_statistics("nonexistent_user")

        assert stats == {}

    def test_conversation_cleanup(self, sample_config):
        """Test conversation cleanup functionality."""
        engine = ConversationEngine(sample_config)

        # Add test conversations
        for user_id in ["user1", "user2", "user3"]:
            engine.conversations[user_id] = {"turns": [], "context": {}}

        # Clean up old conversations (simulate)
        engine.cleanup_old_conversations(days_old=30)

        # Should still have all conversations since they're not old
        assert len(engine.conversations) == 3

    def test_conversation_export_import(self, sample_config, temp_storage_dir):
        """Test conversation export and import functionality."""
        engine = ConversationEngine(sample_config)

        # Add test data
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input="Export test",
            assistant_response="Export response",
            context={"user_id": "user123"},
        )
        engine.add_conversation_turn("user123", turn)

        # Export conversation
        export_file = temp_storage_dir / "export.json"
        engine.export_conversation("user123", str(export_file))

        assert export_file.exists()

        # Import conversation
        new_engine = ConversationEngine(sample_config)
        new_engine.import_conversation(str(export_file))

        assert "user123" in new_engine.conversations
