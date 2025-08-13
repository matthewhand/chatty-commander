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

from .transcription import VoiceTranscriber
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
        **kwargs,
    ):
        self.config_manager = config_manager
        self.command_executor = command_executor
        self.state_manager = state_manager

        # Use mock components if voice deps not available or explicitly requested
        if not VOICE_DEPS_AVAILABLE or use_mock:
            logger.info("Using mock voice components")
            self.wake_detector = MockWakeWordDetector(wake_words=wake_words, **kwargs)
            transcription_backend = "mock"
        else:
            self.wake_detector = WakeWordDetector(wake_words=wake_words, **kwargs)

        self.transcriber = VoiceTranscriber(backend=transcription_backend, **kwargs)

        # State
        self._listening = False
        self._processing = False
        self._callbacks: list[Callable[[str, str], None]] = []  # (command, transcription)

        # Setup wake word detection
        self.wake_detector.add_callback(self._on_wake_word_detected)

        logger.info("Voice pipeline initialized")

    def add_command_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add callback for processed voice commands.

        Args:
            callback: Function called with (command_name, transcription) when command processed
        """
        self._callbacks.append(callback)

    def remove_command_callback(self, callback: Callable[[str, str], None]) -> None:
        """Remove command callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start(self) -> None:
        """Start the voice pipeline."""
        if self._listening:
            logger.warning("Voice pipeline already running")
            return

        try:
            self.wake_detector.start_listening()
            self._listening = True
            logger.info("Voice pipeline started - listening for wake words")

            # Update state if state manager available
            if self.state_manager:
                try:
                    self.state_manager.change_state("voice_listening")
                except Exception as e:
                    logger.debug(f"Could not update state: {e}")

        except Exception as e:
            logger.error(f"Failed to start voice pipeline: {e}")
            raise

    def stop(self) -> None:
        """Stop the voice pipeline."""
        self._listening = False

        try:
            self.wake_detector.stop_listening()
            logger.info("Voice pipeline stopped")

            # Update state if state manager available
            if self.state_manager:
                try:
                    self.state_manager.change_state("idle")
                except Exception as e:
                    logger.debug(f"Could not update state: {e}")

        except Exception as e:
            logger.error(f"Error stopping voice pipeline: {e}")

    def _on_wake_word_detected(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection."""
        if self._processing:
            logger.debug("Already processing voice command, ignoring wake word")
            return

        logger.info(f"Wake word '{wake_word}' detected (confidence: {confidence:.3f})")

        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_voice_command, args=(wake_word,), daemon=True
        )
        thread.start()

    def _process_voice_command(self, wake_word: str) -> None:
        """Process voice command after wake word detection."""
        self._processing = True

        try:
            # Update state
            if self.state_manager:
                try:
                    self.state_manager.change_state("voice_recording")
                except Exception:
                    pass

            # Record and transcribe
            logger.info("Recording voice command...")
            transcription = self.transcriber.record_and_transcribe()

            if not transcription:
                logger.warning("No transcription received")
                return

            logger.info(f"Transcribed: '{transcription}'")

            # Update state
            if self.state_manager:
                try:
                    self.state_manager.change_state("voice_processing")
                except Exception:
                    pass

            # Process command
            command_name = self._match_command(transcription)

            if command_name:
                logger.info(f"Matched command: {command_name}")
                success = self._execute_command(command_name)

                if success:
                    logger.info(f"Successfully executed command: {command_name}")
                    # Notify callbacks
                    self._notify_callbacks(command_name, transcription)
                else:
                    logger.warning(f"Failed to execute command: {command_name}")
            else:
                logger.info(f"No matching command found for: '{transcription}'")
                # Still notify callbacks with empty command name
                self._notify_callbacks("", transcription)

        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
        finally:
            self._processing = False
            # Return to listening state
            if self.state_manager:
                try:
                    self.state_manager.change_state("voice_listening")
                except Exception:
                    pass

    def _match_command(self, transcription: str) -> str | None:
        """Match transcription to available commands."""
        if not self.config_manager:
            logger.debug("No config manager available for command matching")
            return None

        try:
            # Get available commands from config
            model_actions = getattr(self.config_manager, 'model_actions', {})
            if not model_actions:
                logger.debug("No model actions available")
                return None

            # Simple keyword matching (can be enhanced with fuzzy matching, NLP, etc.)
            transcription_lower = transcription.lower()

            # Direct name match first
            for command_name in model_actions.keys():
                if command_name.lower() in transcription_lower:
                    return command_name

            # Keyword-based matching
            command_keywords = {
                "hello": ["hello", "hi", "hey", "greet"],
                "lights": ["lights", "light", "lamp", "illumination"],
                "music": ["music", "song", "play", "audio"],
                "weather": ["weather", "temperature", "forecast"],
                "time": ["time", "clock", "hour"],
                "timer": ["timer", "alarm", "remind"],
            }

            for command_name, keywords in command_keywords.items():
                if command_name in model_actions:
                    for keyword in keywords:
                        if keyword in transcription_lower:
                            return command_name

            return None

        except Exception as e:
            logger.error(f"Error matching command: {e}")
            return None

    def _execute_command(self, command_name: str) -> bool:
        """Execute a matched command."""
        if not self.command_executor:
            logger.debug("No command executor available")
            return False

        try:
            # Execute command through existing command executor
            result = self.command_executor.execute_command(command_name)
            return result is not False  # Consider None as success

        except Exception as e:
            logger.error(f"Error executing command '{command_name}': {e}")
            return False

    def _notify_callbacks(self, command_name: str, transcription: str) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks.copy():
            try:
                callback(command_name, transcription)
            except Exception as e:
                logger.error(f"Error in voice command callback: {e}")

    def trigger_mock_wake_word(self, wake_word: str = "hey_jarvis") -> None:
        """Trigger mock wake word detection (for testing)."""
        if hasattr(self.wake_detector, 'trigger_wake_word'):
            self.wake_detector.trigger_wake_word(wake_word)
        else:
            logger.warning("Mock wake word trigger not available")

    def process_text_command(self, text: str) -> str | None:
        """Process text as if it were a voice command (for testing)."""
        command_name = self._match_command(text)
        if command_name:
            success = self._execute_command(command_name)
            if success:
                self._notify_callbacks(command_name, text)
                return command_name
        return None

    def get_status(self) -> dict[str, any]:
        """Get pipeline status information."""
        return {
            "listening": self._listening,
            "processing": self._processing,
            "wake_detector_available": (
                self.wake_detector.is_listening()
                if hasattr(self.wake_detector, 'is_listening')
                else True
            ),
            "transcriber_available": self.transcriber.is_available(),
            "transcriber_info": self.transcriber.get_backend_info(),
            "available_wake_words": (
                self.wake_detector.get_available_models()
                if hasattr(self.wake_detector, 'get_available_models')
                else []
            ),
        }

    def is_listening(self) -> bool:
        """Check if pipeline is actively listening."""
        return self._listening and not self._processing
