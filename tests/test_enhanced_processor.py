import sys
import os
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from chatty_commander.voice.enhanced_processor import EnhancedVoiceProcessor, VoiceProcessingConfig

class TestEnhancedVoiceProcessor:
    @pytest.fixture
    def processor(self):
        config = VoiceProcessingConfig(sample_rate=16000)
        with patch('logging.getLogger'):
            return EnhancedVoiceProcessor(config)

    def test_initialization(self, processor):
        assert processor is not None
        assert processor.config is not None

    def test_basic_noise_reduction(self, processor):
        # Create dummy audio data
        audio_data = np.random.rand(16000).astype(np.float32)

        # Ensure _basic_noise_reduction is used
        # We need to manually set coefficients if they are not set (e.g. if noisereduce is present)
        if processor._nr_b is None:
             # Manually set them if scipy is available
             try:
                 from scipy import signal
                 processor._nr_b, processor._nr_a = signal.butter(4, 300, btype="high", fs=processor.config.sample_rate)
             except ImportError:
                 pytest.skip("scipy not available")

        result = processor._basic_noise_reduction(audio_data)
        assert result.shape == audio_data.shape
        assert isinstance(result, np.ndarray)

    def test_noise_reduction_initialization_fallback(self):
        config = VoiceProcessingConfig(sample_rate=16000)
        # Test that it falls back to basic noise reduction when noisereduce is missing
        with patch.dict(sys.modules, {'noisereduce': None}):
            with patch('logging.getLogger'):
                # We need to create a new processor here to trigger __init__
                processor = EnhancedVoiceProcessor(config)
                # It might be the bound method or the function itself depending on implementation
                assert processor.noise_reducer == processor._basic_noise_reduction
