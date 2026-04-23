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

Tests intent analysis, sentiment analysis, and prompt building.
"""

from datetime import datetime
from typing import Any

import pytest

from src.chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
    ConversationTurn,
)


@pytest.fixture
def engine():
    """Create a ConversationEngine instance."""
    return ConversationEngine(config={"test": True})


@pytest.fixture
def sample_turn():
    """Create a sample ConversationTurn."""
    return ConversationTurn(
        timestamp=datetime.now(),
        user_input="Hello",
        assistant_response="Hi there!",
        context={"mode": "chatty"},
        sentiment="positive",
        intent="greeting",
    )


class TestConversationTurn:
    """Tests for ConversationTurn dataclass."""

    def test_turn_creation(self, sample_turn):
        """Test creating a ConversationTurn."""
        assert sample_turn.user_input == "Hello"
        assert sample_turn.assistant_response == "Hi there!"
        assert sample_turn.sentiment == "positive"
        assert sample_turn.intent == "greeting"

    def test_turn_defaults(self):
        """Test ConversationTurn default values."""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input="Test",
            assistant_response="Response",
            context={},
        )
        assert turn.sentiment is None
        assert turn.intent is None


class TestIntentAnalysis:
    """Tests for analyze_intent method."""

    def test_mode_switch_intent(self, engine):
        """Test detecting mode switch intent."""
        assert engine.analyze_intent("switch to computer mode") == "mode_switch"
        assert engine.analyze_intent("change mode") == "mode_switch"
        assert engine.analyze_intent("go to idle") == "mode_switch"

    def test_question_intent(self, engine):
        """Test detecting question intent."""
        assert engine.analyze_intent("what is the weather?") == "question"
        assert engine.analyze_intent("how do I do this?") == "question"
        assert engine.analyze_intent("why is the sky blue?") == "question"

    def test_task_request_intent(self, engine):
        """Test detecting task request intent."""
        assert engine.analyze_intent("help me with this") == "task_request"
        assert engine.analyze_intent("create a file") == "task_request"
        assert engine.analyze_intent("do something for me") == "task_request"

    def test_greeting_intent(self, engine):
        """Test detecting greeting intent."""
        assert engine.analyze_intent("hello") == "greeting"
        assert engine.analyze_intent("good morning") == "greeting"
        assert engine.analyze_intent("hey there") == "greeting"

    def test_farewell_intent(self, engine):
        """Test detecting farewell intent."""
        assert engine.analyze_intent("goodbye") == "farewell"
        assert engine.analyze_intent("bye") == "farewell"
        assert engine.analyze_intent("see you later") == "farewell"

    def test_information_seeking_intent(self, engine):
        """Test detecting information seeking intent."""
        assert engine.analyze_intent("tell me about this") == "information_seeking"
        assert engine.analyze_intent("explain how it works") == "information_seeking"
        assert engine.analyze_intent("what is Python?") == "information_seeking"

    def test_general_conversation(self, engine):
        """Test general conversation fallback."""
        # 'tell' in 'random text here' triggers task_request
        assert engine.analyze_intent("12345") == "general_conversation"
        assert engine.analyze_intent("xyz abc") == "general_conversation"


class TestSentimentAnalysis:
    """Tests for analyze_sentiment method."""

    def test_positive_sentiment(self, engine):
        """Test detecting positive sentiment."""
        assert engine.analyze_sentiment("This is great!" "I love this") == "positive"
        assert engine.analyze_sentiment("excellent work") == "positive"
        assert engine.analyze_sentiment("awesome job") == "positive"

    def test_negative_sentiment(self, engine):
        """Test detecting negative sentiment."""
        assert engine.analyze_sentiment("This is terrible") == "negative"
        assert engine.analyze_sentiment("I hate this") == "negative"
        assert engine.analyze_sentiment("awful experience") == "negative"

    def test_neutral_sentiment(self, engine):
        """Test neutral sentiment detection."""
        assert engine.analyze_sentiment("This is okay") == "neutral"
        assert engine.analyze_sentiment("I see") == "neutral"
        assert engine.analyze_sentiment("12345") == "neutral"


class TestConversationContext:
    """Tests for get_conversation_context method."""

    def test_empty_history(self, engine):
        """Test getting context with no history."""
        assert engine.get_conversation_context("user1") == ""

    def test_with_history(self, engine, sample_turn):
        """Test getting context with history."""
        engine.conversation_history["user1"] = [sample_turn]
        context = engine.get_conversation_context("user1")
        assert "Hello" in context
        assert "Hi there!" in context

    def test_context_limit(self, engine):
        """Test context respects limit parameter."""
        # Create 10 turns
        turns = [
            ConversationTurn(
                timestamp=datetime.now(),
                user_input=f"Message {i}",
                assistant_response=f"Response {i}",
                context={},
            )
            for i in range(10)
        ]
        engine.conversation_history["user1"] = turns

        # Get only last 3
        context = engine.get_conversation_context("user1", limit=3)
        assert "Message 9" in context
        assert "Message 0" not in context


class TestEnhancedPrompt:
    """Tests for build_enhanced_prompt method."""

    def test_prompt_contains_user_input(self, engine):
        """Test prompt includes user input."""
        prompt = engine.build_enhanced_prompt(
            "test input", "user1", {"name": "Test"}
        )
        assert "test input" in prompt

    def test_prompt_contains_context(self, engine):
        """Test prompt includes conversation context."""
        engine.conversation_history["user1"] = [
            ConversationTurn(
                timestamp=datetime.now(),
                user_input="Previous",
                assistant_response="Previous response",
                context={},
            )
        ]
        prompt = engine.build_enhanced_prompt(
            "new input", "user1", {"name": "Test"}
        )
        assert "Previous" in prompt

    def test_prompt_with_system_prompt_config(self, engine):
        """Test prompt when persona has system_prompt."""
        prompt = engine.build_enhanced_prompt(
            "hello",
            "user1",
            {"name": "Test", "system_prompt": "You are a helpful assistant."},
        )
        assert "You are a helpful assistant." in prompt
        assert "CONVERSATION CONTEXT:" in prompt

    def test_prompt_without_system_prompt(self, engine):
        """Test prompt without system_prompt uses default."""
        prompt = engine.build_enhanced_prompt(
            "hello", "user1", {"name": "Chatty"}
        )
        assert "You are Chatty" in prompt
        assert "PERSONALITY TRAITS:" in prompt


class TestConversationEngineIntegration:
    """Integration tests for ConversationEngine."""

    def test_full_conversation_flow(self, engine):
        """Test full conversation flow."""
        # Add some history
        engine.conversation_history["user1"] = [
            ConversationTurn(
                timestamp=datetime.now(),
                user_input="Hello",
                assistant_response="Hi!",
                context={},
                intent="greeting",
                sentiment="positive",
            )
        ]

        # Analyze new input
        intent = engine.analyze_intent("how are you?")
        sentiment = engine.analyze_sentiment("I'm doing great!")

        assert intent == "question"
        assert sentiment == "positive"

        # Build prompt
        prompt = engine.build_enhanced_prompt(
            "how are you?", "user1", {"name": "Test"}
        )
        assert "how are you?" in prompt
        assert "Hello" in prompt  # From context


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_string_intent(self, engine):
        """Test intent analysis with empty string."""
        assert engine.analyze_intent("") == "general_conversation"

    def test_empty_string_sentiment(self, engine):
        """Test sentiment analysis with empty string."""
        assert engine.analyze_sentiment("") == "neutral"

    def test_case_insensitive_intent(self, engine):
        """Test intent analysis is case-insensitive."""
        assert engine.analyze_intent("HELLO") == "greeting"
        assert engine.analyze_intent("Switch Mode") == "mode_switch"
