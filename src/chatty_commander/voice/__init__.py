"""
Voice integration module for ChattyCommander.

Provides:
- Wake word detection using OpenWakeWord
- Voice-to-text transcription (local and cloud options)
- Voice command processing pipeline
- Audio input/output management
"""

from .pipeline import VoicePipeline
from .transcription import VoiceTranscriber
from .tts import TextToSpeech
from .wakeword import WakeWordDetector

__all__ = ["WakeWordDetector", "VoiceTranscriber", "VoicePipeline", "TextToSpeech"]
