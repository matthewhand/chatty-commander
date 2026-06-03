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

"""Tests for enhanced voice processor module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
    create_enhanced_voice_processor,
)


class TestVoiceProcessingConfig:
    """Tests for VoiceProcessingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = VoiceProcessingConfig()
        assert config.sample_rate == 16000
        assert config.chunk_size == 1024
        assert config.noise_reduction_enabled is True
        assert config.voice_activity_detection is True
        assert config.echo_cancellation is True
        assert config.auto_gain_control is True
        assert config.confidence_threshold == 0.7
        assert config.silence_timeout == 2.0
        assert config.max_recording_duration == 30.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = VoiceProcessingConfig(
            sample_rate=44100,
            chunk_size=2048,
            noise_reduction_enabled=False,
            confidence_threshold=0.8,
        )
        assert config.sample_rate == 44100
        assert config.chunk_size == 2048
        assert config.noise_reduction_enabled is False
        assert config.confidence_threshold == 0.8


class TestVoiceResult:
    """Tests for VoiceResult dataclass."""

    def test_basic_creation(self):
        """Test basic voice result creation."""
        result = VoiceResult(
            text="hello world",
            confidence=0.95,
            duration=1.5,
            timestamp=datetime.now(),
        )
        assert result.text == "hello world"
        assert result.confidence == 0.95
        assert result.duration == 1.5
        assert result.wake_word_detected is False

    def test_full_creation(self):
        """Test full voice result with all fields."""
        result = VoiceResult(
            text="hello",
            confidence=0.9,
            duration=1.0,
            timestamp=datetime.now(),
            language="en",
            intent="greeting",
            wake_word_detected=True,
        )
        assert result.language == "en"
        assert result.intent == "greeting"
        assert result.wake_word_detected is True


class TestEnhancedVoiceProcessor:
    """Tests for EnhancedVoiceProcessor."""

    def test_initialization_with_defaults(self):
        """Test processor initialization with default config."""
        config = VoiceProcessingConfig()
        processor = EnhancedVoiceProcessor(config)
        assert processor.config == config
        assert processor.is_listening is False
        assert processor.vad_enabled is True

    def test_initialization_with_disabled_vad(self):
        """Test processor with VAD disabled."""
        config = VoiceProcessingConfig(voice_activity_detection=False)
        processor = EnhancedVoiceProcessor(config)
        assert processor.vad_enabled is False


class TestCreateEnhancedVoiceProcessor:
    """Tests for factory function."""

    def test_factory_with_defaults(self):
        """Test factory with default config dict."""
        config = {}
        processor = create_enhanced_voice_processor(config)
        assert isinstance(processor, EnhancedVoiceProcessor)
        assert processor.config.sample_rate == 16000

    def test_factory_with_custom_config(self):
        """Test factory with custom config values."""
        config = {
            "sample_rate": 44100,
            "noise_reduction": False,
            "vad": False,
        }
        processor = create_enhanced_voice_processor(config)
        assert processor.config.sample_rate == 44100
        assert processor.config.noise_reduction_enabled is False
        assert processor.config.voice_activity_detection is False

    def test_factory_all_options(self):
        """Test factory with all config options."""
        config = {
            "sample_rate": 22050,
            "chunk_size": 512,
            "noise_reduction": True,
            "vad": True,
            "echo_cancellation": True,
            "auto_gain": True,
            "confidence_threshold": 0.8,
            "silence_timeout": 3.0,
            "max_duration": 60.0,
        }
        processor = create_enhanced_voice_processor(config)
        assert processor.config.sample_rate == 22050
        assert processor.config.chunk_size == 512
        assert processor.config.confidence_threshold == 0.8
        assert processor.config.silence_timeout == 3.0
        assert processor.config.max_recording_duration == 60.0


class TestEnhancedVoiceProcessorCallbacks:
    """Tests for callback setup."""

    def test_callback_initialization(self):
        """Test that callbacks are initially None."""
        config = VoiceProcessingConfig()
        processor = EnhancedVoiceProcessor(config)
        assert processor.on_speech_start is None
        assert processor.on_speech_end is None
        assert processor.on_transcription is None
        assert processor.on_wake_word is None


class TestEnhancedVoiceProcessorEdgeCases:
    """Edge case tests."""

    def test_zero_confidence_threshold(self):
        """Test with zero confidence threshold."""
        config = VoiceProcessingConfig(confidence_threshold=0.0)
        processor = EnhancedVoiceProcessor(config)
        assert processor.config.confidence_threshold == 0.0

    def test_negative_silence_timeout(self):
        """Test with negative silence timeout."""
        config = VoiceProcessingConfig(silence_timeout=-1.0)
        processor = EnhancedVoiceProcessor(config)
        assert processor.config.silence_timeout == -1.0

    def test_zero_max_duration(self):
        """Test with zero max recording duration."""
        config = VoiceProcessingConfig(max_recording_duration=0.0)
        processor = EnhancedVoiceProcessor(config)
        assert processor.config.max_recording_duration == 0.0
