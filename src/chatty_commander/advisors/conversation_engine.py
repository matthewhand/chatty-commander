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

"""Advanced conversation engine for ChattyCommander AI interactions.

TODO: This is an experimental implementation that needs testing and validation.
TODO: Verify conversation context management works correctly.
TODO: Test sentiment and intent analysis accuracy.
TODO: Validate persona-based prompt generation.
TODO: Confirm conversation memory persistence.
TODO: Test fallback responses in various scenarios.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""

    timestamp: datetime
    user_input: str
    assistant_response: str
    context: dict[str, Any]
    sentiment: str | None = None
    intent: str | None = None


class ConversationEngine:
    """Advanced conversation engine with context awareness and personality."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.conversation_history: dict[str, list[ConversationTurn]] = {}
        self.user_preferences: dict[str, dict[str, Any]] = {}

    def analyze_intent(self, text: str) -> str:
        """Analyze user intent from text."""
        if text is None:
            return "general_conversation"
        text_lower = text.lower()

        # Command intents
        if any(word in text_lower for word in ["switch", "change", "go to"]):
            if "mode" in text_lower:
                return "mode_switch"

        # Question intents
        if text.startswith(("what", "how", "why", "when", "where", "who")):
            return "question"

        # Task intents
        if any(
            word in text_lower for word in ["help", "assist", "do", "make", "create"]
        ):
            return "task_request"

        # Social intents
        if any(
            word in text_lower
            for word in ["hello", "hi", "hey", "good morning", "good afternoon"]
        ):
            return "greeting"

        if any(
            word in text_lower for word in ["bye", "goodbye", "see you", "farewell"]
        ):
            return "farewell"

        # Information seeking
        if any(
            word in text_lower for word in ["tell me", "explain", "describe", "what is"]
        ):
            return "information_seeking"

        return "general_conversation"

    def analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        if text is None:
            return "neutral"
        positive_words = [
            "good",
            "great",
            "awesome",
            "excellent",
            "love",
            "like",
            "happy",
            "pleased",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "hate",
            "dislike",
            "sad",
            "angry",
            "frustrated",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def get_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """Get recent conversation context for a user."""
        if user_id not in self.conversation_history:
            return ""

        recent_turns = self.conversation_history[user_id][-limit:]
        context_lines = []

        for turn in recent_turns:
            context_lines.append(f"User: {turn.user_input}")
            context_lines.append(f"Assistant: {turn.assistant_response}")

        return "\n".join(context_lines)

    def build_enhanced_prompt(
        self,
        user_input: str,
        user_id: str,
        persona_config: dict[str, Any],
        current_mode: str = "chatty",
    ) -> str:
        """Build an enhanced prompt with context, personality, and intelligence."""
        # Analyze current input
        intent = self.analyze_intent(user_input)
        sentiment = self.analyze_sentiment(user_input)

        # Get conversation history
        context = self.get_conversation_context(user_id)

        # Get user preferences
        preferences = self.user_preferences.get(user_id, {})

        # Build persona prompt
        persona_name = persona_config.get("name", "Chatty")
        persona_traits = persona_config.get(
            "traits", ["friendly", "helpful", "knowledgeable", "conversational"]
        )
        persona_style = persona_config.get("style", "casual and engaging")

        # Build system prompt - use persona system_prompt if available, otherwise build default
        if "system_prompt" in persona_config:
            base_system_prompt = persona_config["system_prompt"]
            # Add context and analysis to the persona's system prompt
            system_prompt = f"""{base_system_prompt}

CONVERSATION CONTEXT:
{context if context else "This is the start of our conversation."}

CURRENT ANALYSIS:
- User Intent: {intent}
- Sentiment: {sentiment}

INSTRUCTIONS:
1. Respond naturally and conversationally
2. Remember context from our conversation
3. If asked to switch modes, use: SWITCH_MODE:mode_name
4. Be helpful but also engaging and personable
5. Adapt your response style to the user's sentiment"""
        else:
            # Fallback to default system prompt
            system_prompt = f"""You are {persona_name}, an advanced AI assistant with the following characteristics:

PERSONALITY TRAITS: {', '.join(persona_traits)}
COMMUNICATION STYLE: {persona_style}
CURRENT MODE: {current_mode}

CAPABILITIES:
- Voice conversation with natural speech patterns
- 3D avatar with expressive responses
- Mode switching (idle, computer, chatty modes)
- Intelligent task assistance
- Contextual memory and learning

CONVERSATION CONTEXT:
{context if context else "This is the start of our conversation."}

USER PREFERENCES: {json.dumps(preferences) if preferences else "None learned yet"}

CURRENT ANALYSIS:
- User Intent: {intent}
- Sentiment: {sentiment}

INSTRUCTIONS:
1. Respond naturally and conversationally
2. Remember context from our conversation
3. If asked to switch modes, use: SWITCH_MODE:mode_name
4. Be helpful but also engaging and personable
5. Adapt your response style to the user's sentiment
6. For greetings, be warm and welcoming
7. For questions, be informative but conversational
8. For tasks, be helpful and offer step-by-step guidance

Remember: You're not just answering questions - you're having a conversation with a human who values both intelligence and personality."""

        return f"{system_prompt}\n\nUser: {user_input}\n\nAssistant:"

    def record_conversation_turn(
        self,
        user_id: str,
        user_input: str,
        assistant_response: str,
        context: dict[str, Any],
    ):
        """Record a conversation turn for future context."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            assistant_response=assistant_response,
            context=context,
            sentiment=self.analyze_sentiment(user_input),
            intent=self.analyze_intent(user_input),
        )

        self.conversation_history[user_id].append(turn)

        # Keep only last 50 turns per user to manage memory
        if len(self.conversation_history[user_id]) > 50:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -50:
            ]

    def update_user_preferences(self, user_id: str, preferences: dict[str, Any]):
        """Update user preferences based on conversation patterns."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)

    def get_smart_fallback_response(
        self, user_input: str, intent: str, sentiment: str
    ) -> str:
        """Generate intelligent fallback responses when LLM is unavailable."""
        if intent == "greeting":
            return "Hello! I'm Chatty, your AI assistant. I'm excited to chat with you! While my full AI capabilities are still loading, I'm here to help however I can."

        elif intent == "farewell":
            return "Goodbye! It was wonderful chatting with you. I hope to talk again soon!"

        elif intent == "mode_switch":
            if "computer" in user_input.lower():
                return "I'll switch you to computer mode for system tasks. SWITCH_MODE:computer"
            elif "idle" in user_input.lower():
                return "Switching to idle mode for voice commands. SWITCH_MODE:idle"
            else:
                return "I can help you switch modes! Try saying 'switch to computer mode' or 'switch to idle mode'."

        elif intent == "question":
            return f"That's a great question about '{user_input}'. I'd love to give you a detailed answer, but I need my full AI backend configured to provide the intelligent response you deserve. In the meantime, I'm here to chat!"

        elif intent == "task_request":
            return "I'm designed to help with all sorts of tasks! Once my AI backend is fully configured, I'll be able to assist with complex requests, provide detailed guidance, and even help with creative projects."

        elif intent == "information_seeking":
            return "I love sharing knowledge! While I'm waiting for my full AI capabilities to come online, I can tell you that I'm designed to be your intelligent companion for voice conversations, system control, and creative assistance."

        elif sentiment == "negative":
            return "I can sense you might be frustrated, and I understand. I'm still getting my full capabilities online, but I'm here to help however I can right now. What's on your mind?"

        elif sentiment == "positive":
            return "I love your positive energy! It makes me excited to chat with you. Once my full AI backend is configured, we'll be able to have even more engaging conversations!"

        else:
            return f"I hear you saying '{user_input}' and I want to give you a thoughtful response. I'm an AI assistant designed for natural conversation, but I need my backend configured to show you my full potential. What would you like to know about me?"


def create_conversation_engine(config: dict[str, Any]) -> ConversationEngine:
    """Factory function to create a conversation engine."""
    return ConversationEngine(config)
