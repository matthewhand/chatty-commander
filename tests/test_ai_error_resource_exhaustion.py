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
Error handling and edge case tests for resource exhaustion scenarios in AI components.
Tests dependency failures, invalid inputs, network issues, resource exhaustion,
and graceful degradation scenarios across IntelligenceCore, VoiceProcessor, and ConversationEngine.
"""

import queue
from unittest.mock import patch

from chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
)
from chatty_commander.ai.intelligence_core import AIResponse, IntelligenceCore
from chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
)


class TestResourceExhaustion:
    """Test handling of resource exhaustion scenarios."""

    def test_memory_exhaustion_handling(self):
        """Test handling when system memory is exhausted."""
        conversation_engine = ConversationEngine({"max_history_length": 1000})

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Mock memory allocation failure
        with patch(
            "chatty_commander.advisors.conversation_engine.deepcopy"
        ) as mock_deepcopy:
            mock_deepcopy.side_effect = MemoryError("Out of memory")

            with patch.object(conversation_engine, "logger") as mock_logger:
                response = intelligence_core.process_text_input(
                    "Test memory exhaustion"
                )

                # Should handle gracefully
                assert isinstance(response, AIResponse)
                mock_logger.error.assert_called()

    def test_disk_space_exhaustion_handling(self):
        """Test handling when disk space is exhausted."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

        # Mock disk space exhaustion
        with patch("os.path.getsize", side_effect=OSError("No space left on device")):
            with patch.object(voice_processor, "logger") as mock_logger:
                result = voice_processor.process_audio_file("large_audio.wav")

                assert result is None or isinstance(result, VoiceResult)
                mock_logger.error.assert_called()

    def test_cpu_resource_exhaustion_handling(self):
        """Test handling when CPU resources are exhausted."""
        intelligence_core = IntelligenceCore()

        # Mock CPU-intensive operation timeout
        with patch.object(intelligence_core, "_analyze_intent") as mock_analyze:
            mock_analyze.side_effect = TimeoutError("CPU timeout")

            with patch.object(intelligence_core, "logger") as mock_logger:
                response = intelligence_core.process_text_input(
                    "Complex analysis request"
                )

                assert isinstance(response, AIResponse)
                assert response.success is True or response.success is False
                mock_logger.warning.assert_called() or mock_logger.error.assert_called()

    def test_thread_pool_exhaustion_handling(self):
        """Test handling when thread pool is exhausted."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

        # Mock thread creation failure
        with patch("threading.Thread") as mock_thread:
            mock_thread.side_effect = RuntimeError("Can't start new thread")

            with patch.object(voice_processor, "logger") as mock_logger:
                # Try to start audio processing loop
                voice_processor.start_listening()

                # Should handle gracefully
                mock_logger.error.assert_called()
                assert voice_processor.listening_active is False

    def test_queue_overflow_handling(self):
        """Test handling of queue overflow scenarios."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

        # Create a queue with limited size
        voice_processor.audio_queue = queue.Queue(maxsize=5)

        # Fill the queue to capacity
        for i in range(10):
            try:
                voice_processor.audio_queue.put_nowait(f"audio_data_{i}")
            except queue.Full:
                # Expected behavior when queue is full
                pass

        # Test that processor handles full queue gracefully
        with patch.object(voice_processor, "logger") as mock_logger:
            voice_processor._process_audio_chunk(b"new_audio_data")

            # Should handle gracefully
            mock_logger.warning.assert_called() or mock_logger.info.assert_called()

    def test_file_handle_exhaustion_handling(self):
        """Test handling when file handles are exhausted."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

        # Mock file opening failure
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Too many open files")

            with patch.object(voice_processor, "logger") as mock_logger:
                result = voice_processor.process_audio_file("test.wav")

                assert result is None or isinstance(result, VoiceResult)
                mock_open.assert_called()
                mock_logger.error.assert_called()
