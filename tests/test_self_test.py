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

"""Tests for voice self-test module."""

from unittest.mock import MagicMock, patch

import pytest

from src.chatty_commander.voice.self_test import VoiceSelfTester


class TestVoiceSelfTester:
    """Tests for VoiceSelfTester class."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester()
            assert tester.transcriber is not None
            assert tester.openai_client is None
            assert len(tester.test_phrases) > 0

    def test_initialization_with_transcriber(self):
        """Test initialization with provided transcriber."""
        mock_transcriber = MagicMock()
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester(transcriber=mock_transcriber)
            assert tester.transcriber == mock_transcriber

    def test_initialization_with_api_key(self):
        """Test initialization with OpenAI API key."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            with patch("src.chatty_commander.voice.self_test.OPENAI_AVAILABLE", True):
                with patch("src.chatty_commander.voice.self_test.OpenAI") as mock_openai:
                    tester = VoiceSelfTester(openai_api_key="test-key")
                    mock_openai.assert_called_once_with(api_key="test-key")

    def test_initialization_with_test_phrases(self):
        """Test initialization with custom test phrases."""
        custom_phrases = ["hello", "world"]
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester(test_phrases=custom_phrases)
            assert tester.test_phrases == custom_phrases


class TestVoiceSelfTesterDefaultPhrases:
    """Tests for default test phrases."""

    def test_default_phrases_exist(self):
        """Test that default phrases are populated."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester()
            assert len(tester.test_phrases) > 0
            assert all(isinstance(p, str) for p in tester.test_phrases)

    def test_default_phrases_not_empty(self):
        """Test that default phrases are not empty strings."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester()
            assert all(len(p.strip()) > 0 for p in tester.test_phrases)


class TestVoiceSelfTesterMockMode:
    """Tests for mock/CI mode operation."""

    def test_no_tts_when_unavailable(self):
        """Test that TTS is not initialized when unavailable."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester()
            assert tester._tts_engine is None

    def test_no_openai_when_unavailable(self):
        """Test that OpenAI client is not created when unavailable."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            with patch("src.chatty_commander.voice.self_test.OPENAI_AVAILABLE", False):
                tester = VoiceSelfTester(openai_api_key="test-key")
                assert tester.openai_client is None


class TestVoiceSelfTesterEdgeCases:
    """Edge case tests."""

    def test_empty_test_phrases_uses_defaults(self):
        """Test that empty test phrases list uses default phrases."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester(test_phrases=[])
            # Empty list is falsy, so defaults are used
            assert len(tester.test_phrases) > 0

    def test_single_test_phrase(self):
        """Test with single test phrase."""
        with patch("src.chatty_commander.voice.self_test.TTS_AVAILABLE", False):
            tester = VoiceSelfTester(test_phrases=["only phrase"])
            assert tester.test_phrases == ["only phrase"]
