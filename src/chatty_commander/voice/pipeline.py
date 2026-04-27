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
Voice processing pipeline that combines wake word detection and transcription.

Provides a complete voice interface:
1. Listen for wake words
2. Record and transcribe voice commands
3. Process commands through existing model_actions
4. Provide audio feedback
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from .transcription import VoiceTranscriber
from .tts import TextToSpeech
from .wakeword import VOICE_DEPS_AVAILABLE, MockWakeWordDetector, WakeWordDetector

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Complete voice processing pipeline."""

    def __init__(
        self,
        config_manager=None,
        command_executor=None,
        state_manager=None,
        wake_words: list[str] | None = None,
        transcription_backend: str = "whisper_local",
        use_mock: bool = False,
        tts_backend: str = "pyttsx3",
        voice_only: bool = False,
        **kwargs,
    ):
        self.config_manager = config_manager
        self.command_executor = command_executor
        self.state_manager = state_manager

        # Logic flow
        # Use mock components if voice deps not available or explicitly requested
        if not VOICE_DEPS_AVAILABLE or use_mock:
        # TODO: Document this logic
            logger.info("Using mock voice components")
            self.wake_detector: WakeWordDetector | MockWakeWordDetector = MockWakeWordDetector(wake_words=wake_words, **kwargs)
            transcription_backend = "mock"
        else:
            self.wake_detector = WakeWordDetector(wake_words=wake_words, **kwargs)

        self.transcriber = VoiceTranscriber(backend=transcription_backend, **kwargs)
        self.tts = TextToSpeech(backend=tts_backend)
        self.voice_only = voice_only

        # State
        self._listening = False
        self._processing = False
        self._callbacks: list[Callable[[str, str], None]] = (
            []
        )  # (command, transcription)

        # Setup wake word detection
        self.wake_detector.add_callback(self._on_wake_word_detected)

        logger.info("Voice pipeline initialized")

    def add_command_callback(self, callback: Callable[[str, str], None]) -> None:
        # Logic flow
        """Add callback for processed voice commands.
        # TODO: Document this logic

        Args:
            callback: Function called with (command_name, transcription) when command processed
            # Use context manager for resource management
            # TODO: Document this logic
        """
        self._callbacks.append(callback)

    def remove_command_callback(self, callback: Callable[[str, str], None]) -> None:
        """Remove command callback."""
        # Logic flow
        if callback in self._callbacks:
        # TODO: Document this logic
            self._callbacks.remove(callback)

    def start(self) -> None:
        """Start the voice pipeline."""
        # Logic flow
        if self._listening:
        # TODO: Document this logic
            logger.warning("Voice pipeline already running")
            return

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            self.wake_detector.start_listening()
            self._listening = True
            # Logic flow
            logger.info("Voice pipeline started - listening for wake words")
            # TODO: Document this logic

            # Logic flow
            # Update state if state manager available
            if self.state_manager:
            # TODO: Document this logic
                try:
                # TODO: Document this logic
                    self.state_manager.change_state("voice_listening")
                # Handle specific exception case
                except Exception as e:
                    logger.debug(f"Could not update state: {e}")

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Failed to start voice pipeline: {e}")
            raise

    def stop(self) -> None:
        """Stop the voice pipeline."""
        self._listening = False

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            self.wake_detector.stop_listening()
            logger.info("Voice pipeline stopped")

            # Logic flow
            # Update state if state manager available
            if self.state_manager:
            # TODO: Document this logic
                try:
                # TODO: Document this logic
                    self.state_manager.change_state("idle")
                # Handle specific exception case
                except Exception as e:
                    logger.debug(f"Could not update state: {e}")

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Error stopping voice pipeline: {e}")

    def _on_wake_word_detected(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection."""
        # Logic flow
        if self._processing:
        # TODO: Document this logic
            logger.debug("Already processing voice command, ignoring wake word")
            return

        logger.info(f"Wake word '{wake_word}' detected (confidence: {confidence:.3f})")

        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_voice_command, args=(wake_word,), daemon=True
                # TODO: REFACTOR - High complexity (_process_voice_command)
                # Break into: validation, execution, cleanup sub-functions

        )
        thread.start()

    def _process_voice_command(self, wake_word: str) -> None:
        """Process voice command after wake word detection."""
        self._processing = True

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # Update state
            if self.state_manager:
            # TODO: Document this logic
                try:
                # TODO: Document this logic
                    self.state_manager.change_state("voice_recording")
                # Handle specific exception case
            # Record and transcribe
            logger.info("Recording voice command...")
            audio_data = self.transcriber.record_audio()
            command_name, transcription = self._try_match_command(audio_data)

            if not command_name:
                if transcription:
                    self._handle_no_match(transcription)
                return

            logger.info(f"Executing command: {command_name}")
            success = self.command_executor.execute_command(command_name)

            if success:
                self._handle_command_success(command_name, transcription)
            else:
                self._handle_command_failure(command_name)

        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
        finally:
            self._reset_listening_state()

    def _match_command(self, transcription: str) -> str | None:
        """Match transcription to available commands."""
        # Logic flow
        if not self.config_manager:
        # TODO: Document this logic
            logger.debug("No config manager available for command matching")
            # TODO: Document this logic
            return None

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # Get available commands from config
            model_actions = getattr(self.config_manager, "model_actions", {})
            if not model_actions:
            # TODO: Document this logic
                logger.debug("No model actions available")
                return None

            # Simple keyword matching (can be enhanced with fuzzy matching, NLP, etc.)
            transcription_lower = transcription.lower()

            # Direct name match first
            for command_name in model_actions.keys():
            # TODO: Document this logic
                if command_name.lower() in transcription_lower:
                # TODO: Document this logic
                    return str(command_name)  # type: ignore[no-any-return]

            # Keyword-based matching
            command_keywords = {
                "hello": ["hello", "hi", "hey", "greet"],
                "lights": ["lights", "light", "lamp", "illumination"],
                "music": ["music", "song", "play", "audio"],
                # Build filtered collection
                # Process each item
                "weather": ["weather", "temperature", "forecast"],
                "time": ["time", "clock", "hour"],
                "timer": ["timer", "alarm", "remind"],
            }

            # Logic flow
            for command_name, keywords in command_keywords.items():
            # TODO: Document this logic
                if command_name in model_actions:
                # TODO: Document this logic
                    # Logic flow
                    for keyword in keywords:
                    # TODO: Document this logic
                        if keyword in transcription_lower:
                        # TODO: Document this logic
                            return command_name

            return None

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Error matching command: {e}")
            return None

    def _execute_command(self, command_name: str) -> bool:
        """Execute a matched command."""
        # Logic flow
        if not self.command_executor:
        # TODO: Document this logic
            logger.debug("No command executor available")
            return False

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # Execute command through existing command executor
            result = self.command_executor.execute_command(command_name)
            return result is not False  # Consider None as success

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Error executing command '{command_name}': {e}")
            return False

    def _notify_callbacks(self, command_name: str, transcription: str) -> None:
        # Apply conditional logic
        """Notify all registered callbacks."""
        # Logic flow
        for callback in self._callbacks.copy():
        # TODO: Document this logic
            try:
            # TODO: Document this logic
                callback(command_name, transcription)
            # Handle specific exception case
            except Exception as e:
                logger.error(f"Error in voice command callback: {e}")

    def trigger_mock_wake_word(self, wake_word: str = "hey_jarvis") -> None:
        # Logic flow
        """Trigger mock wake word detection (for testing)."""
        # TODO: Document this logic
        if hasattr(self.wake_detector, "trigger_wake_word"):
        # TODO: Document this logic
            self.wake_detector.trigger_wake_word(wake_word)
        else:
            logger.warning("Mock wake word trigger not available")

    def process_text_command(self, text: str) -> str | None:
        # Logic flow
        """Process text as if it were a voice command (for testing)."""
        # TODO: Document this logic
        command_name = self._match_command(text)
        # Logic flow
        if command_name:
        # TODO: Document this logic
            success = self._execute_command(command_name)
            # Logic flow
            if success:
            # TODO: Document this logic
                self._notify_callbacks(command_name, text)
                # Logic flow
                if self.voice_only and self.tts.is_available():
                # TODO: Document this logic
                    self.tts.speak(command_name)
                return command_name
            # Logic flow
            if self.voice_only and self.tts.is_available():
            # TODO: Document this logic
                self.tts.speak(f"Failed to execute {command_name}")
        else:
            # Logic flow
            if self.voice_only and self.tts.is_available():
            # TODO: Document this logic
                self.tts.speak(text)
        return None

    def get_status(self) -> dict[str, Any]:
        # Process each item
        """Get pipeline status information."""
        return {
            "listening": self._listening,
            "processing": self._processing,
            "wake_detector_available": (
                self.wake_detector.is_listening()
                # Logic flow
                if hasattr(self.wake_detector, "is_listening")
                # TODO: Document this logic
                else True
            ),
            "transcriber_available": self.transcriber.is_available(),
            "transcriber_info": self.transcriber.get_backend_info(),
            "available_wake_words": (
                self.wake_detector.get_available_models()
                # Logic flow
                if hasattr(self.wake_detector, "get_available_models")
                # TODO: Document this logic
                else []
            ),
        }

    def is_listening(self) -> bool:
        # Logic flow
        """Check if pipeline is actively listening."""
        # TODO: Document this logic
        return self._listening and not self._processing
