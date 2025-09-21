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
Exhaustive test coverage for ConversationEngine.
Tests all functionality including context management, sentiment analysis, intent detection,
prompt building, fallback responses, and error handling.
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
    ConversationTurn,
    create_conversation_engine,
)


class TestConversationTurn:
    """Test ConversationTurn data class."""

    def test_conversation_turn_creation(self):
        """Test creating ConversationTurn with all fields."""
        timestamp = datetime.now()
        turn = ConversationTurn(
            role="user",
            content="Hello, how are you?",
            timestamp=timestamp,
            intent="greeting",
            sentiment="positive",
            confidence=0.95,
            context_data={"user_name": "John", "location": "office"},
        )

        assert turn.role == "user"
        assert turn.content == "Hello, how are you?"
        assert turn.timestamp == timestamp
        assert turn.intent == "greeting"
        assert turn.sentiment == "positive"
        assert turn.confidence == 0.95
        assert turn.context_data == {"user_name": "John", "location": "office"}

    def test_conversation_turn_minimal(self):
        """Test creating ConversationTurn with minimal fields."""
        turn = ConversationTurn(role="assistant", content="I'm doing well, thank you!")

        assert turn.role == "assistant"
        assert turn.content == "I'm doing well, thank you!"
        assert turn.intent is None
        assert turn.sentiment is None
        assert turn.confidence == 0.0
        assert turn.context_data == {}

    def test_conversation_turn_to_dict(self):
        """Test converting ConversationTurn to dictionary."""
        turn = ConversationTurn(
            role="user",
            content="Test message",
            intent="question",
            sentiment="neutral",
            confidence=0.8,
        )

        turn_dict = turn.to_dict()

        assert isinstance(turn_dict, dict)
        assert turn_dict["role"] == "user"
        assert turn_dict["content"] == "Test message"
        assert turn_dict["intent"] == "question"
        assert turn_dict["sentiment"] == "neutral"
        assert turn_dict["confidence"] == 0.8
        assert "timestamp" in turn_dict


class TestConversationEngineInitialization:
    """Test ConversationEngine initialization and setup."""

    def test_default_initialization(self):
        """Test engine initialization with default settings."""
        engine = ConversationEngine()

        assert engine.conversation_history == []
        assert engine.max_history_length == 50
        assert engine.user_preferences == {}
        assert engine.context_window == 10
        assert engine.fallback_enabled is True
        assert engine.debug_mode is False
        assert engine.conversation_context == {}

    def test_custom_initialization(self):
        """Test engine initialization with custom settings."""
        engine = ConversationEngine(
            max_history_length=100,
            context_window=20,
            fallback_enabled=False,
            debug_mode=True,
            initial_preferences={"theme": "dark", "language": "en"},
        )

        assert engine.max_history_length == 100
        assert engine.context_window == 20
        assert engine.fallback_enabled is False
        assert engine.debug_mode is True
        assert engine.user_preferences == {"theme": "dark", "language": "en"}

    def test_initialization_with_llm_client(self):
        """Test engine initialization with LLM client."""
        mock_llm_client = Mock()
        engine = ConversationEngine(llm_client=mock_llm_client)

        assert engine.llm_client == mock_llm_client

    @patch("chatty_commander.advisors.conversation_engine.logging.getLogger")
    def test_debug_mode_logging_setup(self, mock_get_logger):
        """Test logging setup in debug mode."""
        engine = ConversationEngine(debug_mode=True)

        mock_get_logger.assert_called_once()


class TestIntentAnalysis:
    """Test intent analysis functionality."""

    def test_greeting_intent_detection(self):
        """Test detection of greeting intents."""
        engine = ConversationEngine()

        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "howdy",
            "what's up",
        ]

        for greeting in greetings:
            intent, confidence = engine.analyze_intent(greeting)
            assert intent == "greeting"
            assert confidence > 0.7

    def test_question_intent_detection(self):
        """Test detection of question intents."""
        engine = ConversationEngine()

        questions = [
            "what is the weather?",
            "how do I do this?",
            "where are you?",
            "when will it happen?",
            "why is this important?",
            "who are you?",
        ]

        for question in questions:
            intent, confidence = engine.analyze_intent(question)
            assert intent == "question"
            assert confidence > 0.6

    def test_command_intent_detection(self):
        """Test detection of command intents."""
        engine = ConversationEngine()

        commands = [
            "turn on the lights",
            "open the door",
            "close window",
            "start music",
            "stop playback",
            "take screenshot",
        ]

        for command in commands:
            intent, confidence = engine.analyze_intent(command)
            assert intent == "command"
            assert confidence > 0.6

    def test_farewell_intent_detection(self):
        """Test detection of farewell intents."""
        engine = ConversationEngine()

        farewells = ["goodbye", "bye", "see you later", "farewell", "talk to you soon"]

        for farewell in farewells:
            intent, confidence = engine.analyze_intent(farewell)
            assert intent == "farewell"
            assert confidence > 0.7

    def test_unknown_intent_detection(self):
        """Test detection of unknown/unclear intents."""
        engine = ConversationEngine()

        unclear_inputs = ["asdf", "12345", "...", "???", "", "um", "uh"]

        for unclear in unclear_inputs:
            intent, confidence = engine.analyze_intent(unclear)
            assert intent == "unknown"
            assert confidence < 0.5

    def test_intent_detection_case_insensitive(self):
        """Test that intent detection is case insensitive."""
        engine = ConversationEngine()

        test_cases = [
            ("HELLO", "greeting"),
            ("Hello", "greeting"),
            ("hElLo", "greeting"),
            ("TURN ON LIGHTS", "command"),
            ("Turn On Lights", "command"),
        ]

        for text, expected_intent in test_cases:
            intent, confidence = engine.analyze_intent(text)
            assert intent == expected_intent
            assert confidence > 0.6

    def test_intent_detection_with_context(self):
        """Test intent detection with conversation context."""
        engine = ConversationEngine()

        # Add conversation context
        engine.conversation_context = {"current_topic": "weather"}

        # Test contextual intent
        intent, confidence = engine.analyze_intent("will it rain today?")
        assert intent == "question"
        assert confidence > 0.7  # Should be higher with context

    def test_intent_detection_empty_input(self):
        """Test intent detection with empty input."""
        engine = ConversationEngine()

        intent, confidence = engine.analyze_intent("")
        assert intent == "unknown"
        assert confidence == 0.0

    def test_intent_detection_none_input(self):
        """Test intent detection with None input."""
        engine = ConversationEngine()

        intent, confidence = engine.analyze_intent(None)
        assert intent == "unknown"
        assert confidence == 0.0


class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""

    def test_positive_sentiment_detection(self):
        """Test detection of positive sentiment."""
        engine = ConversationEngine()

        positive_texts = [
            "I love this!",
            "This is amazing!",
            "Great job!",
            "I'm so happy",
            "Excellent work",
            "Wonderful!",
        ]

        for text in positive_texts:
            sentiment, confidence = engine.analyze_sentiment(text)
            assert sentiment == "positive"
            assert confidence > 0.6

    def test_negative_sentiment_detection(self):
        """Test detection of negative sentiment."""
        engine = ConversationEngine()

        negative_texts = [
            "I hate this",
            "This is terrible",
            "Awful job",
            "I'm so angry",
            "Very bad",
            "Horrible!",
        ]

        for text in negative_texts:
            sentiment, confidence = engine.analyze_sentiment(text)
            assert sentiment == "negative"
            assert confidence > 0.6

    def test_neutral_sentiment_detection(self):
        """Test detection of neutral sentiment."""
        engine = ConversationEngine()

        neutral_texts = [
            "The weather is sunny",
            "I see a book",
            "There is a table",
            "The meeting is at 3pm",
            "Code review completed",
        ]

        for text in neutral_texts:
            sentiment, confidence = engine.analyze_sentiment(text)
            assert sentiment == "neutral"
            assert confidence > 0.5

    def test_mixed_sentiment_detection(self):
        """Test detection of mixed/sentiment."""
        engine = ConversationEngine()

        mixed_texts = [
            "I love the idea but hate the implementation",
            "Good effort but needs improvement",
            "Not bad, could be better",
        ]

        for text in mixed_texts:
            sentiment, confidence = engine.analyze_sentiment(text)
            # Mixed sentiment should be classified as neutral or with lower confidence
            assert sentiment in ["neutral", "mixed"] or confidence < 0.7

    def test_sentiment_detection_with_emojis(self):
        """Test sentiment detection with emojis."""
        engine = ConversationEngine()

        emoji_texts = [
            ("I'm happy today 😊", "positive"),
            ("This is sad 😢", "negative"),
            ("Great news! 🎉", "positive"),
            ("Oh no! 😱", "negative"),
        ]

        for text, expected_sentiment in emoji_texts:
            sentiment, confidence = engine.analyze_sentiment(text)
            assert sentiment == expected_sentiment
            assert confidence > 0.5

    def test_sentiment_detection_empty_input(self):
        """Test sentiment detection with empty input."""
        engine = ConversationEngine()

        sentiment, confidence = engine.analyze_sentiment("")
        assert sentiment == "neutral"
        assert confidence == 0.0

    def test_sentiment_detection_none_input(self):
        """Test sentiment detection with None input."""
        engine = ConversationEngine()

        sentiment, confidence = engine.analyze_sentiment(None)
        assert sentiment == "neutral"
        assert confidence == 0.0


class TestConversationHistory:
    """Test conversation history management."""

    def test_record_conversation_turn(self):
        """Test recording a conversation turn."""
        engine = ConversationEngine()

        turn = ConversationTurn(
            role="user", content="Hello", intent="greeting", sentiment="positive"
        )

        engine.record_conversation_turn(turn)

        assert len(engine.conversation_history) == 1
        assert engine.conversation_history[0] == turn

    def test_record_multiple_turns(self):
        """Test recording multiple conversation turns."""
        engine = ConversationEngine()

        turns = [
            ConversationTurn(role="user", content="Hello"),
            ConversationTurn(role="assistant", content="Hi there!"),
            ConversationTurn(role="user", content="How are you?"),
            ConversationTurn(role="assistant", content="I'm doing well!"),
        ]

        for turn in turns:
            engine.record_conversation_turn(turn)

        assert len(engine.conversation_history) == 4
        assert engine.conversation_history == turns

    def test_history_length_limit(self):
        """Test that history respects maximum length limit."""
        engine = ConversationEngine(max_history_length=3)

        # Add more turns than the limit
        for i in range(5):
            turn = ConversationTurn(role="user", content=f"Message {i}")
            engine.record_conversation_turn(turn)

        # Should only keep the last 3 turns
        assert len(engine.conversation_history) == 3
        assert engine.conversation_history[0].content == "Message 2"
        assert engine.conversation_history[2].content == "Message 4"

    def test_get_conversation_context(self):
        """Test getting conversation context."""
        engine = ConversationEngine(context_window=3)

        # Add some conversation history
        for i in range(5):
            turn = ConversationTurn(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                intent="test",
            )
            engine.record_conversation_turn(turn)

        context = engine.get_conversation_context()

        assert len(context) == 3  # Should return context_window size
        assert context[0].content == "Message 2"
        assert context[2].content == "Message 4"

    def test_get_empty_conversation_context(self):
        """Test getting context when history is empty."""
        engine = ConversationEngine()

        context = engine.get_conversation_context()

        assert context == []

    def test_clear_conversation_history(self):
        """Test clearing conversation history."""
        engine = ConversationEngine()

        # Add some history
        engine.record_conversation_turn(ConversationTurn(role="user", content="Test"))
        assert len(engine.conversation_history) == 1

        # Clear history
        engine.clear_conversation_history()

        assert len(engine.conversation_history) == 0

    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        engine = ConversationEngine()

        # Add conversation turns with different intents
        turns = [
            ConversationTurn(role="user", content="Hello", intent="greeting"),
            ConversationTurn(role="assistant", content="Hi!", intent="greeting"),
            ConversationTurn(role="user", content="Turn on lights", intent="command"),
            ConversationTurn(role="assistant", content="Done!", intent="confirmation"),
        ]

        for turn in turns:
            engine.record_conversation_turn(turn)

        summary = engine.get_conversation_summary()

        assert "Total turns: 4" in summary
        assert "greeting: 2" in summary
        assert "command: 1" in summary
        assert "confirmation: 1" in summary


class TestUserPreferences:
    """Test user preference management."""

    def test_update_user_preferences(self):
        """Test updating user preferences."""
        engine = ConversationEngine()

        preferences = {"theme": "dark", "language": "en", "timezone": "EST"}

        engine.update_user_preferences(preferences)

        assert engine.user_preferences == preferences

    def test_update_existing_preferences(self):
        """Test updating existing user preferences."""
        engine = ConversationEngine()

        # Set initial preferences
        engine.user_preferences = {"theme": "light", "language": "en"}

        # Update with new preferences
        new_preferences = {"theme": "dark", "timezone": "PST"}
        engine.update_user_preferences(new_preferences)

        # Should merge preferences
        expected = {"theme": "dark", "language": "en", "timezone": "PST"}
        assert engine.user_preferences == expected

    def test_get_user_preferences(self):
        """Test getting user preferences."""
        engine = ConversationEngine()

        preferences = {"theme": "dark", "language": "en"}
        engine.user_preferences = preferences

        retrieved_preferences = engine.get_user_preferences()

        assert retrieved_preferences == preferences

    def test_preferences_in_context(self):
        """Test that preferences are included in conversation context."""
        engine = ConversationEngine()

        # Set user preferences
        engine.user_preferences = {"theme": "dark", "language": "en"}

        # Add conversation turn
        turn = ConversationTurn(role="user", content="Change theme")
        engine.record_conversation_turn(turn)

        # Build enhanced prompt
        prompt = engine.build_enhanced_prompt("Make it light theme")

        # Should include user preferences in context
        assert "dark" in prompt or "theme" in prompt


class TestEnhancedPromptBuilding:
    """Test enhanced prompt building functionality."""

    def test_basic_prompt_building(self):
        """Test building a basic enhanced prompt."""
        engine = ConversationEngine()

        prompt = engine.build_enhanced_prompt("Hello")

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_with_conversation_context(self):
        """Test building prompt with conversation context."""
        engine = ConversationEngine()

        # Add conversation history
        engine.record_conversation_turn(
            ConversationTurn(role="user", content="What's the weather?")
        )
        engine.record_conversation_turn(
            ConversationTurn(role="assistant", content="It's sunny")
        )

        prompt = engine.build_enhanced_prompt("Will it rain tomorrow?")

        # Should include conversation history
        assert "weather" in prompt.lower() or "sunny" in prompt.lower()

    def test_prompt_with_user_preferences(self):
        """Test building prompt with user preferences."""
        engine = ConversationEngine()

        # Set user preferences
        engine.user_preferences = {"location": "New York", "units": "imperial"}

        prompt = engine.build_enhanced_prompt("What's the temperature?")

        # Should include user preferences
        assert "New York" in prompt or "imperial" in prompt

    def test_prompt_with_current_context(self):
        """Test building prompt with current context."""
        engine = ConversationEngine()

        # Set current context
        engine.conversation_context = {
            "current_task": "weather_query",
            "location": "Boston",
        }

        prompt = engine.build_enhanced_prompt("Will it be cold?")

        # Should include current context
        assert "weather" in prompt.lower() or "Boston" in prompt

    def test_prompt_with_intent_and_sentiment(self):
        """Test building prompt with intent and sentiment analysis."""
        engine = ConversationEngine()

        prompt = engine.build_enhanced_prompt("I love this feature! It's amazing!")

        # Should include sentiment information
        assert "positive" in prompt.lower() or "love" in prompt.lower()

    def test_prompt_with_llm_client(self):
        """Test building prompt with LLM client integration."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.return_value = "Enhanced response"

        engine = ConversationEngine(llm_client=mock_llm_client)

        prompt = engine.build_enhanced_prompt("Complex question")

        # Should attempt to use LLM client
        mock_llm_client.generate_response.assert_called_once()

    def test_prompt_building_empty_input(self):
        """Test building prompt with empty input."""
        engine = ConversationEngine()

        prompt = engine.build_enhanced_prompt("")

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_building_none_input(self):
        """Test building prompt with None input."""
        engine = ConversationEngine()

        prompt = engine.build_enhanced_prompt(None)

        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestSmartFallbackResponses:
    """Test smart fallback response generation."""

    def test_greeting_fallback_response(self):
        """Test fallback response for greeting intent."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response("Hello", intent="greeting")

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            word in response.lower() for word in ["hello", "hi", "hey", "greeting"]
        )

    def test_question_fallback_response(self):
        """Test fallback response for question intent."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response("What's this?", intent="question")

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            phrase in response.lower()
            for phrase in ["i'm not sure", "could you clarify", "don't have enough"]
        )

    def test_command_fallback_response(self):
        """Test fallback response for command intent."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response(
            "Turn on lights", intent="command"
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            phrase in response.lower()
            for phrase in ["i can't", "unable to", "don't have access"]
        )

    def test_farewell_fallback_response(self):
        """Test fallback response for farewell intent."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response("Goodbye", intent="farewell")

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            word in response.lower()
            for word in ["goodbye", "bye", "see you", "farewell"]
        )

    def test_unknown_fallback_response(self):
        """Test fallback response for unknown intent."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response("asdf", intent="unknown")

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            phrase in response.lower()
            for phrase in ["i don't understand", "could you rephrase", "not sure what"]
        )

    def test_fallback_response_with_context(self):
        """Test fallback response with conversation context."""
        engine = ConversationEngine()

        # Add conversation context
        engine.record_conversation_turn(
            ConversationTurn(role="user", content="What's the weather?")
        )

        response = engine.get_smart_fallback_response(
            "Will it rain?", intent="question"
        )

        assert isinstance(response, str)
        assert len(response) > 0

    def test_fallback_response_with_sentiment(self):
        """Test fallback response considering user sentiment."""
        engine = ConversationEngine()

        # Test with negative sentiment
        response = engine.get_smart_fallback_response(
            "This is terrible!", intent="unknown", sentiment="negative"
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should be more empathetic for negative sentiment
        assert any(
            phrase in response.lower() for phrase in ["sorry", "understand", "help"]
        )

    def test_fallback_disabled(self):
        """Test behavior when fallback is disabled."""
        engine = ConversationEngine(fallback_enabled=False)

        response = engine.get_smart_fallback_response("Hello", intent="greeting")

        assert response == ""

    def test_fallback_response_empty_input(self):
        """Test fallback response with empty input."""
        engine = ConversationEngine()

        response = engine.get_smart_fallback_response("", intent="unknown")

        assert isinstance(response, str)
        assert len(response) > 0


class TestContextAwareness:
    """Test context awareness and management."""

    def test_context_from_conversation_flow(self):
        """Test extracting context from conversation flow."""
        engine = ConversationEngine()

        # Simulate conversation about weather
        engine.record_conversation_turn(
            ConversationTurn(
                role="user", content="What's the weather in Boston?", intent="question"
            )
        )
        engine.record_conversation_turn(
            ConversationTurn(
                role="assistant", content="It's sunny and 75°F", intent="answer"
            )
        )
        engine.record_conversation_turn(
            ConversationTurn(
                role="user", content="Will it rain tomorrow?", intent="question"
            )
        )

        # Context should include location and topic
        context = engine.conversation_context
        assert "weather" in str(context).lower() or "Boston" in str(context)

    def test_context_persistence_across_turns(self):
        """Test that context persists across conversation turns."""
        engine = ConversationEngine()

        # Set initial context
        engine.conversation_context = {"topic": "music", "genre": "jazz"}

        # Add new turn
        engine.record_conversation_turn(
            ConversationTurn(role="user", content="Play some music", intent="command")
        )

        # Context should still contain previous information
        assert "topic" in engine.conversation_context
        assert "music" in str(engine.conversation_context).lower()

    def test_context_clearing(self):
        """Test clearing conversation context."""
        engine = ConversationEngine()

        # Set some context
        engine.conversation_context = {"topic": "weather", "location": "Boston"}

        # Clear context
        engine.clear_conversation_context()

        assert engine.conversation_context == {}

    def test_context_from_user_preferences(self):
        """Test context derived from user preferences."""
        engine = ConversationEngine()

        # Set user preferences
        engine.user_preferences = {
            "default_location": "New York",
            "preferred_units": "imperial",
            "language": "en",
        }

        # Context should include user preferences
        prompt = engine.build_enhanced_prompt("What's the temperature?")

        assert "New York" in prompt or "imperial" in prompt


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_intent_analysis_with_exception(self):
        """Test intent analysis when processing fails."""
        engine = ConversationEngine()

        # Mock an internal processing error
        with patch.object(engine, "logger") as mock_logger:
            with patch.object(
                engine, "_extract_keywords", side_effect=Exception("Processing error")
            ):
                intent, confidence = engine.analyze_intent("test")

                assert intent == "unknown"
                assert confidence == 0.0
                mock_logger.error.assert_called_once()

    def test_sentiment_analysis_with_exception(self):
        """Test sentiment analysis when processing fails."""
        engine = ConversationEngine()

        with patch.object(engine, "logger") as mock_logger:
            with patch.object(
                engine,
                "_analyze_text_sentiment",
                side_effect=Exception("Sentiment error"),
            ):
                sentiment, confidence = engine.analyze_sentiment("test")

                assert sentiment == "neutral"
                assert confidence == 0.0
                mock_logger.error.assert_called_once()

    def prompt_building_with_llm_failure(self):
        """Test prompt building when LLM client fails."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception("LLM error")

        engine = ConversationEngine(llm_client=mock_llm_client)

        with patch.object(engine, "logger") as mock_logger:
            prompt = engine.build_enhanced_prompt("test")

            # Should fall back to basic prompt
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            mock_logger.error.assert_called_once()

    def test_conversation_history_corruption_recovery(self):
        """Test recovery from corrupted conversation history."""
        engine = ConversationEngine()

        # Add some valid turns
        engine.record_conversation_turn(ConversationTurn(role="user", content="Hello"))

        # Simulate corruption
        engine.conversation_history.append("invalid_turn")

        with patch.object(engine, "logger") as mock_logger:
            # Should handle gracefully when getting context
            context = engine.get_conversation_context()

            # Should filter out invalid entries
            assert len(context) == 1
            assert context[0].content == "Hello"
            mock_logger.warning.assert_called()

    def test_invalid_user_preferences(self):
        """Test handling of invalid user preferences."""
        engine = ConversationEngine()

        # Try to set invalid preferences
        with patch.object(engine, "logger") as mock_logger:
            engine.update_user_preferences("invalid_preferences")

            # Should not crash, preferences should remain unchanged or empty
            assert isinstance(engine.user_preferences, dict)
            mock_logger.error.assert_called_once()

    def test_memory_limit_exceeded(self):
        """Test handling when memory limits are exceeded."""
        engine = ConversationEngine(max_history_length=5)

        # Add many turns to exceed memory limit
        for i in range(100):
            turn = ConversationTurn(role="user", content=f"Message {i}")
            engine.record_conversation_turn(turn)

        # Should only keep the configured limit
        assert len(engine.conversation_history) == 5
        assert engine.conversation_history[-1].content == "Message 99"


class TestPerformanceAndStress:
    """Test performance and stress scenarios."""

    def test_large_conversation_history_performance(self):
        """Test performance with large conversation history."""
        engine = ConversationEngine(max_history_length=1000)

        # Add large conversation history
        start_time = time.time()
        for i in range(500):
            turn = ConversationTurn(
                role="user" if i % 2 == 0 else "assistant",
                content=f"This is a test message number {i} with some longer content to make it realistic",
                intent="test",
                sentiment="neutral",
            )
            engine.record_conversation_turn(turn)

        add_time = time.time() - start_time

        # Should be reasonably fast
        assert add_time < 1.0
        assert len(engine.conversation_history) == 500

    def test_rapid_intent_analysis(self):
        """Test rapid intent analysis requests."""
        engine = ConversationEngine()

        test_inputs = [
            "Hello",
            "What's the weather?",
            "Turn on lights",
            "Goodbye",
            "How are you?",
            "Play music",
        ] * 50  # 300 total requests

        start_time = time.time()
        results = []
        for text in test_inputs:
            intent, confidence = engine.analyze_intent(text)
            results.append((intent, confidence))

        analysis_time = time.time() - start_time

        # Should complete reasonably fast
        assert analysis_time < 2.0
        assert len(results) == 300

    def test_memory_efficiency_with_context(self):
        """Test memory efficiency with context building."""
        engine = ConversationEngine(context_window=20)

        # Add conversation turns with rich context
        for i in range(100):
            turn = ConversationTurn(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i} with detailed information about topic {i % 10}",
                intent=f"intent_{i % 5}",
                sentiment="positive" if i % 3 == 0 else "neutral",
                context_data={"topic": f"topic_{i % 10}", "detail": f"detail_{i}"},
            )
            engine.record_conversation_turn(turn)

        # Build enhanced prompt
        start_time = time.time()
        prompt = engine.build_enhanced_prompt("Tell me about the topics we discussed")
        build_time = time.time() - start_time

        # Should be fast and memory efficient
        assert build_time < 0.1
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_concurrent_operations(self):
        """Test concurrent operations on conversation engine."""
        engine = ConversationEngine()

        results = []

        def add_turns():
            for i in range(20):
                turn = ConversationTurn(role="user", content=f"Message {i}")
                engine.record_conversation_turn(turn)
                results.append(f"Added turn {i}")

        def analyze_intents():
            for i in range(20):
                intent, confidence = engine.analyze_intent(f"Test message {i}")
                results.append(f"Analyzed intent: {intent}")

        def build_prompts():
            for i in range(20):
                prompt = engine.build_enhanced_prompt(f"Prompt {i}")
                results.append(f"Built prompt length: {len(prompt)}")

        # Run concurrent operations
        import threading

        threads = [
            threading.Thread(target=add_turns),
            threading.Thread(target=analyze_intents),
            threading.Thread(target=build_prompts),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should complete without crashes
        assert len(results) == 60


class TestFactoryFunction:
    """Test the create_conversation_engine factory function."""

    def test_factory_default_config(self):
        """Test factory function with default configuration."""
        engine = create_conversation_engine()

        assert isinstance(engine, ConversationEngine)
        assert engine.max_history_length == 50
        assert engine.context_window == 10
        assert engine.fallback_enabled is True

    def test_factory_with_custom_config(self):
        """Test factory function with custom configuration."""
        config = {
            "max_history_length": 100,
            "context_window": 15,
            "fallback_enabled": False,
            "debug_mode": True,
            "initial_preferences": {"theme": "dark"},
        }

        engine = create_conversation_engine(config)

        assert isinstance(engine, ConversationEngine)
        assert engine.max_history_length == 100
        assert engine.context_window == 15
        assert engine.fallback_enabled is False
        assert engine.debug_mode is True
        assert engine.user_preferences == {"theme": "dark"}

    def test_factory_with_llm_client(self):
        """Test factory function with LLM client."""
        mock_llm_client = Mock()
        config = {"llm_client": mock_llm_client}

        engine = create_conversation_engine(config)

        assert isinstance(engine, ConversationEngine)
        assert engine.llm_client == mock_llm_client

    def test_factory_with_invalid_config(self):
        """Test factory function with invalid configuration."""
        with pytest.raises(TypeError):
            create_conversation_engine("invalid_config")

    def test_factory_with_partial_config(self):
        """Test factory function with partial configuration."""
        config = {"max_history_length": 75, "debug_mode": True}

        engine = create_conversation_engine(config)

        assert engine.max_history_length == 75
        assert engine.debug_mode is True
        # Other values should be defaults
        assert engine.context_window == 10
        assert engine.fallback_enabled is True
