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

from . import matching
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

        # Use mock components if voice deps not available or explicitly requested
        if not VOICE_DEPS_AVAILABLE or use_mock:
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
        # Guards the check-and-set of ``_processing`` so two wake words arriving
        # in quick succession cannot both pass the "already processing?" check
        # and spawn competing recorder threads contending for the microphone.
        self._processing_lock = threading.Lock()
        # Keep a reference to the most recently spawned worker so it is not a
        # fully untracked daemon thread (aids join-on-stop / debugging).
        self._processing_thread: threading.Thread | None = None
        self._callbacks: list[Callable[[str, str], None]] = (
            []
        )  # (command, transcription)

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
            self._try_change_state("voice_listening")

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
            self._try_change_state("idle")

        except Exception as e:
            logger.error(f"Error stopping voice pipeline: {e}")

    def _on_wake_word_detected(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection."""
        # Atomically claim the processing slot: check-and-set ``_processing``
        # under the lock so two rapid detections cannot both spawn a recorder.
        with self._processing_lock:
            if self._processing:
                logger.debug("Already processing voice command, ignoring wake word")
                return
            self._processing = True

        logger.info(f"Wake word '{wake_word}' detected (confidence: {confidence:.3f})")

        # Start processing in background thread (tracked, not fully orphaned).
        thread = threading.Thread(
            target=self._process_voice_command, args=(wake_word,), daemon=True
        )
        self._processing_thread = thread
        thread.start()

    def _safe_change_state(self, new_state: str) -> None:
        """Safely attempt a state change if a state_manager is present.

        Duplicated try/except pattern existed in _process_voice_command (and stop).
        Extracted to reduce complexity while preserving exact prior behavior
        (swallow exceptions, no logging in the hot path for these states).
        """
        if self.state_manager:
            try:
                self.state_manager.change_state(new_state)
            except Exception:
                pass

    def _try_change_state(self, new_state: str) -> None:
        """Attempt state manager change with debug log on failure.

        Extracted from duplicated inline code in start() and stop() to reduce
        duplication while preserving exact behavior and debug logging.
        (Contrast to _safe_change_state which is silent.)
        """
        if self.state_manager:
            try:
                self.state_manager.change_state(new_state)
            except Exception as e:
                logger.debug(f"Could not update state: {e}")

    def _handle_matched_command(self, command_name: str, transcription: str) -> bool:
        """Handle the matched command execution, notify, and TTS feedback path.

        Extracted from _process_voice_command to lower complexity and
        eliminate duplicated TTS/notify logic.
        Returns the success status from execute_command for callers that need it.
        """
        logger.info(f"Matched command: {command_name}")
        success = self._execute_command(command_name)

        if success:
            logger.info(f"Successfully executed command: {command_name}")
            self._notify_callbacks(command_name, transcription)
            if self.voice_only and self.tts.is_available():
                self.tts.speak(command_name)
        else:
            logger.warning(f"Failed to execute command: {command_name}")
            if self.voice_only and self.tts.is_available():
                self.tts.speak(f"Failed to execute {command_name}")
        return success

    def _handle_unmatched_transcription(self, transcription: str) -> None:
        """Handle the no-match case (notify callbacks + optional TTS)."""
        logger.info(f"No matching command found for: '{transcription}'")
        self._notify_callbacks("", transcription)
        if self.voice_only and self.tts.is_available():
            self.tts.speak("Sorry, I didn't understand that")

    def _process_voice_command(self, wake_word: str) -> None:
        """Process voice command after wake word detection."""
        self._processing = True

        try:
            self._safe_change_state("voice_recording")

            logger.info("Recording voice command...")
            transcription = self.transcriber.record_and_transcribe()

            if not transcription:
                logger.warning("No transcription received")
                return

            logger.info(f"Transcribed: '{transcription}'")

            self._safe_change_state("voice_processing")

            command_name = self._match_command(transcription)

            if command_name:
                self._handle_matched_command(command_name, transcription)
            else:
                self._handle_unmatched_transcription(transcription)

        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
        finally:
            self._processing = False
            self._safe_change_state("voice_listening")

    def _match_command(self, transcription: str) -> str | None:
        """Match transcription to available commands."""
        if not self.config_manager:
            logger.debug("No config manager available for command matching")
            return None

        try:
            model_actions = getattr(self.config_manager, "model_actions", {})
            if not model_actions:
                logger.debug("No model actions available")
                return None

            transcription_lower = transcription.lower()

            # Direct name match first (delegated to extracted pure helper)
            match = self._find_direct_name_match(transcription_lower, model_actions)
            if match:
                return match

            # Keyword-based matching (extracted helper to keep _match_command short)
            match = self._match_by_keywords(transcription_lower, model_actions)
            if match:
                return match

            return None

        except Exception as e:
            logger.error(f"Error matching command: {e}")
            return None

    @staticmethod
    def _matches_phrase(phrase: str, tokens: list[str]) -> bool:
        """Return True if ``phrase`` appears as a whole word/phrase in ``tokens``.

        Word-boundary aware matching (not naive substring) so that a command
        named "play" does not match words like "replay"/"display"/"player", and
        an underscore-joined command name like "play_music" matches the spoken
        phrase "play music". Single-word phrases require an exact token; multi-
        word phrases require the token sequence to appear contiguously.

        Delegates to :mod:`chatty_commander.voice.matching` — the single shared
        matcher used by both this pipeline and the dry-run voice-test pipeline,
        so the two cannot drift.
        """
        return matching.matches_phrase(phrase, tokens)

    def _match_by_keywords(self, transcription_lower: str, model_actions: dict) -> str | None:
        """Keyword-based matching extracted from _match_command.

        Only considers keywords for commands that exist in current model_actions.
        Uses word-boundary matching so keywords match whole words only.
        Delegates to the shared :mod:`chatty_commander.voice.matching` helpers.
        """
        tokens = matching.tokenize(transcription_lower)
        command_keywords = self._get_keyword_map()
        for command_name, keywords in command_keywords.items():
            if command_name in model_actions:
                for keyword in keywords:
                    if self._matches_phrase(keyword, tokens):
                        return command_name
        return None

    def _get_keyword_map(self) -> dict[str, list[str]]:
        """Return the keyword mapping used for fuzzy command matching.

        Delegates to the canonical table in
        :mod:`chatty_commander.voice.matching` so the real pipeline and the
        dry-run voice-test pipeline share one source of truth.
        """
        return matching.get_keyword_map()

    def _find_direct_name_match(self, transcription_lower: str, model_actions: dict) -> str | None:
        """Direct name (whole-word/phrase) match extracted from _match_command.

        Pure helper. Matches command names against the transcription with
        word-boundary awareness (via :meth:`_matches_phrase`) rather than naive
        substring containment, so underscore-joined names like "play_music"
        match the spoken phrase "play music now" while "play" does not match
        "replay". Delegates tokenization/matching to the shared module.
        """
        tokens = matching.tokenize(transcription_lower)
        for command_name in model_actions.keys():
            if self._matches_phrase(str(command_name), tokens):
                return str(command_name)
        return None

    def _execute_command(self, command_name: str) -> bool:
        """Execute a matched command."""
        if not self.command_executor:
            logger.debug("No command executor available")
            return False

        try:
            result = self.command_executor.execute_command(command_name)
            return result is not False
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
        if hasattr(self.wake_detector, "trigger_wake_word"):
            self.wake_detector.trigger_wake_word(wake_word)
        else:
            logger.warning("Mock wake word trigger not available")

    def process_text_command(self, text: str) -> str | None:
        """Process a text command directly (bypassing wake word).

        Reuses the same matched/unmatched handlers as the voice wake path
        to avoid duplication of notify/TTS/execute logic.
        """
        command_name = self._match_command(text)
        if command_name:
            success = self._handle_matched_command(command_name, text)
            if success:
                return command_name
            # failure feedback (speak) already performed inside handler
        else:
            self._handle_unmatched_transcription(text)
        return None

    def _get_wake_detector_available(self) -> bool:
        """Small extracted helper from get_status (continuing voice/pipeline qa #1 complexity reduction)."""
        if hasattr(self.wake_detector, "is_listening"):
            return bool(self.wake_detector.is_listening())
        return True

    def _get_available_wake_words(self) -> list[str]:
        """Small extracted helper from get_status (continuing voice/pipeline qa #1 complexity reduction)."""
        if hasattr(self.wake_detector, "get_available_models"):
            models = self.wake_detector.get_available_models()
            return list(models) if models else []
        return []

    def get_status(self) -> dict[str, Any]:
        return {
            "listening": self._listening,
            "processing": self._processing,
            "wake_detector_available": self._get_wake_detector_available(),
            "transcriber_available": self.transcriber.is_available(),
            "transcriber_info": self.transcriber.get_backend_info(),
            "available_wake_words": self._get_available_wake_words(),
        }

    def is_listening(self) -> bool:
        """Check if pipeline is actively listening."""
        return self._listening and not self._processing

