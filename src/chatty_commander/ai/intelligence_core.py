"""Core AI intelligence module that orchestrates all AI capabilities."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..advisors.service import AdvisorMessage, AdvisorsService
from ..app.config import Config
from ..app.state_manager import StateManager
from ..voice.enhanced_processor import VoiceResult, create_enhanced_voice_processor


@dataclass
class AIResponse:
    """Response from the AI intelligence core."""

    text: str
    confidence: float
    intent: str
    actions: list[dict[str, Any]]
    metadata: dict[str, Any]
    timestamp: datetime


class IntelligenceCore:
    """Core AI intelligence that orchestrates voice, conversation, and actions."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.advisors_service = AdvisorsService(config)
        self.voice_processor = None
        self.state_manager = StateManager()

        # AI state
        self.current_conversation_context = {}
        self.active_persona = "chatty"
        self.listening_mode = "continuous"  # continuous, push-to-talk, wake-word

        # Callbacks
        self.on_response: Callable[[AIResponse], None] | None = None
        self.on_mode_change: Callable[[str], None] | None = None
        self.on_error: Callable[[str], None] | None = None

        self._initialize_voice_processing()

    def _initialize_voice_processing(self):
        """Initialize enhanced voice processing."""
        try:
            voice_config = {
                "sample_rate": 16000,
                "noise_reduction": True,
                "vad": True,
                "confidence_threshold": 0.7,
                "silence_timeout": 2.0,
            }

            self.voice_processor = create_enhanced_voice_processor(voice_config)

            # Set up voice callbacks
            self.voice_processor.on_transcription = self._handle_voice_input
            self.voice_processor.on_wake_word = self._handle_wake_word
            self.voice_processor.on_speech_start = self._handle_speech_start
            self.voice_processor.on_speech_end = self._handle_speech_end

            self.logger.info("Voice processing initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize voice processing: {e}")
            self.voice_processor = None

    def _handle_voice_input(self, voice_result: VoiceResult):
        """Handle transcribed voice input."""
        try:
            if voice_result.confidence < 0.5:
                self.logger.debug(f"Low confidence voice input ignored: {voice_result.text}")
                return

            self.logger.info(
                f"Voice input: {voice_result.text} (confidence: {voice_result.confidence})"
            )

            # Process through AI
            response = self.process_input(
                text=voice_result.text,
                input_type="voice",
                metadata={
                    "confidence": voice_result.confidence,
                    "duration": voice_result.duration,
                    "language": voice_result.language,
                    "wake_word_detected": voice_result.wake_word_detected,
                },
            )

            # Trigger response callback
            if self.on_response:
                self.on_response(response)

        except Exception as e:
            self.logger.error(f"Error handling voice input: {e}")
            if self.on_error:
                self.on_error(f"Voice processing error: {e}")

    def _handle_wake_word(self, wake_word: str):
        """Handle wake word detection."""
        self.logger.info(f"Wake word detected: {wake_word}")

        # Determine target mode based on wake word
        mode_map = {
            "hey chatty": "chatty",
            "chatty": "chatty",
            "hey computer": "computer",
            "computer": "computer",
        }

        target_mode = mode_map.get(wake_word.lower(), "chatty")

        # Switch mode if needed
        if self.state_manager.current_state != target_mode:
            try:
                self.state_manager.change_state(target_mode)
                if self.on_mode_change:
                    self.on_mode_change(target_mode)
                self.logger.info(f"Switched to {target_mode} mode via wake word")
            except Exception as e:
                self.logger.error(f"Failed to switch mode: {e}")

    def _handle_speech_start(self):
        """Handle start of speech detection."""
        self.logger.debug("Speech started")
        # Could trigger visual feedback here

    def _handle_speech_end(self):
        """Handle end of speech detection."""
        self.logger.debug("Speech ended")
        # Could trigger processing indicator here

    def process_input(
        self, text: str, input_type: str = "text", metadata: dict[str, Any] | None = None
    ) -> AIResponse:
        """Process any input through the AI intelligence core."""
        start_time = datetime.now()
        metadata = metadata or {}

        try:
            # Create advisor message
            advisor_message = AdvisorMessage(
                platform="voice" if input_type == "voice" else "text",
                channel="main",
                user="user",
                text=text,
                username="User",
                metadata=metadata,
            )

            # Process through advisors service
            advisor_reply = self.advisors_service.handle_message(advisor_message)

            # Analyze the response for actions
            actions = self._extract_actions(advisor_reply.reply)
            intent = self._analyze_intent(text)

            # Create AI response
            response = AIResponse(
                text=advisor_reply.reply,
                confidence=metadata.get("confidence", 1.0),
                intent=intent,
                actions=actions,
                metadata={
                    "persona_id": advisor_reply.persona_id,
                    "model": advisor_reply.model,
                    "api_mode": advisor_reply.api_mode,
                    "context_key": advisor_reply.context_key,
                    "input_type": input_type,
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    **metadata,
                },
                timestamp=start_time,
            )

            # Execute any actions
            self._execute_actions(actions)

            return response

        except Exception as e:
            self.logger.error(f"Error processing input: {e}")

            # Return error response
            return AIResponse(
                text=f"I apologize, but I encountered an error processing your request: {str(e)}",
                confidence=0.0,
                intent="error",
                actions=[],
                metadata={"error": str(e), "input_type": input_type},
                timestamp=start_time,
            )

    def _analyze_intent(self, text: str) -> str:
        """Analyze user intent from text."""
        text_lower = text.lower()

        # Mode switching
        if (
            any(word in text_lower for word in ['switch', 'change', 'go to'])
            and 'mode' in text_lower
        ):
            return 'mode_switch'

        # System commands
        if any(word in text_lower for word in ['screenshot', 'capture', 'take picture']):
            return 'screenshot'

        if any(word in text_lower for word in ['lights on', 'turn on lights']):
            return 'lights_on'

        if any(word in text_lower for word in ['lights off', 'turn off lights']):
            return 'lights_off'

        # Questions
        if text.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
            return 'question'

        # Greetings
        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'good morning']):
            return 'greeting'

        # Tasks
        if any(word in text_lower for word in ['help', 'assist', 'do', 'make', 'create']):
            return 'task_request'

        return 'conversation'

    def _extract_actions(self, response_text: str) -> list[dict[str, Any]]:
        """Extract actionable commands from AI response."""
        actions = []

        # Look for mode switch commands
        if "SWITCH_MODE:" in response_text:
            import re

            matches = re.findall(r'SWITCH_MODE:(\w+)', response_text)
            for mode in matches:
                actions.append(
                    {"type": "mode_switch", "target_mode": mode.strip(), "priority": "high"}
                )

        # Look for system commands
        if "✓ Switched to" in response_text:
            actions.append({"type": "mode_switched", "priority": "info"})

        # Look for other action patterns
        action_patterns = {
            r'take.*screenshot': {"type": "screenshot", "priority": "medium"},
            r'lights.*on': {"type": "lights_on", "priority": "medium"},
            r'lights.*off': {"type": "lights_off", "priority": "medium"},
        }

        import re

        for pattern, action in action_patterns.items():
            if re.search(pattern, response_text.lower()):
                actions.append(action)

        return actions

    def _execute_actions(self, actions: list[dict[str, Any]]):
        """Execute extracted actions."""
        for action in actions:
            try:
                action_type = action.get("type")

                if action_type == "mode_switch":
                    target_mode = action.get("target_mode")
                    if target_mode:
                        self.state_manager.change_state(target_mode)
                        if self.on_mode_change:
                            self.on_mode_change(target_mode)
                        self.logger.info(f"Executed mode switch to {target_mode}")

                elif action_type == "screenshot":
                    # Trigger screenshot command
                    self.logger.info("Executing screenshot command")
                    # Could integrate with command executor here

                elif action_type in ["lights_on", "lights_off"]:
                    self.logger.info(f"Executing {action_type} command")
                    # Could integrate with home automation here

            except Exception as e:
                self.logger.error(f"Failed to execute action {action}: {e}")

    def start_voice_listening(self):
        """Start continuous voice listening."""
        if self.voice_processor:
            self.voice_processor.start_listening()
            self.listening_mode = "continuous"
            self.logger.info("Started continuous voice listening")
        else:
            self.logger.warning("Voice processor not available")

    def stop_voice_listening(self):
        """Stop voice listening."""
        if self.voice_processor:
            self.voice_processor.stop_listening()
            self.listening_mode = "off"
            self.logger.info("Stopped voice listening")

    def process_text_input(self, text: str) -> AIResponse:
        """Process text input directly."""
        return self.process_input(text, input_type="text")

    def process_voice_file(self, file_path: str) -> AIResponse:
        """Process an audio file."""
        if not self.voice_processor:
            return AIResponse(
                text="Voice processing not available",
                confidence=0.0,
                intent="error",
                actions=[],
                metadata={"error": "No voice processor"},
                timestamp=datetime.now(),
            )

        try:
            voice_result = self.voice_processor.process_audio_file(file_path)
            return self.process_input(
                text=voice_result.text,
                input_type="voice_file",
                metadata={
                    "confidence": voice_result.confidence,
                    "duration": voice_result.duration,
                    "file_path": file_path,
                },
            )
        except Exception as e:
            self.logger.error(f"Error processing voice file: {e}")
            return AIResponse(
                text=f"Error processing voice file: {e}",
                confidence=0.0,
                intent="error",
                actions=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(),
            )

    def set_persona(self, persona_id: str):
        """Change the active AI persona."""
        self.active_persona = persona_id
        self.logger.info(f"Changed persona to {persona_id}")

    def get_conversation_stats(self) -> dict[str, Any]:
        """Get statistics about current conversation."""
        return {
            "active_persona": self.active_persona,
            "current_mode": self.state_manager.current_state,
            "listening_mode": self.listening_mode,
            "voice_available": self.voice_processor is not None,
            "advisors_enabled": self.advisors_service.enabled,
        }

    def shutdown(self):
        """Shutdown the intelligence core."""
        self.stop_voice_listening()
        self.logger.info("Intelligence core shutdown")


def create_intelligence_core(config: Config) -> IntelligenceCore:
    """Factory function to create the intelligence core."""
    return IntelligenceCore(config)
