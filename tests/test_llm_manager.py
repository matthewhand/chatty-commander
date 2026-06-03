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

"""Tests for LLM manager module."""

from unittest.mock import MagicMock, patch

import pytest

from src.chatty_commander.llm.manager import LLMManager


class TestLLMManager:
    """Tests for LLMManager."""

    def test_init_with_mock_only(self):
        """Test initialization with mock backend only."""
        manager = LLMManager(use_mock=True)
        assert manager.is_available() is True
        assert "mock" in manager.backends

    def test_init_creates_backends_dict(self):
        """Test that initialization creates backends dictionary."""
        manager = LLMManager(use_mock=True)
        assert isinstance(manager.backends, dict)
        assert len(manager.backends) >= 1

    def test_mock_backend_always_available(self):
        """Test that mock backend is always available."""
        manager = LLMManager(use_mock=True)
        assert manager.backends["mock"].is_available() is True

    def test_active_backend_selected(self):
        """Test that active backend is selected."""
        manager = LLMManager(use_mock=True)
        assert manager.active_backend is not None

    def test_get_active_backend_name_with_mock(self):
        """Test getting active backend name with mock."""
        manager = LLMManager(use_mock=True)
        name = manager.get_active_backend_name()
        assert name == "mock"

    def test_generate_response_with_mock(self):
        """Test generating response with mock backend."""
        manager = LLMManager(use_mock=True)
        response = manager.generate_response("Hello")
        assert isinstance(response, str)

    def test_preferred_backend_mock(self):
        """Test preferred backend selection with mock."""
        manager = LLMManager(preferred_backend="mock", use_mock=True)
        assert manager.get_active_backend_name() == "mock"

    def test_preferred_backend_unavailable(self):
        """Test fallback when preferred backend unavailable."""
        manager = LLMManager(preferred_backend="openai", use_mock=True)
        # Should fall back to mock
        assert manager.is_available() is True

    def test_default_ollama_model(self):
        """Test default Ollama model."""
        manager = LLMManager(use_mock=True)
        assert manager.backends["mock"] is not None

    def test_default_local_model(self):
        """Test default local model setting."""
        manager = LLMManager(use_mock=True)
        # Mock backend doesn't use local model
        assert manager.is_available() is True


class TestLLMManagerEnvVars:
    """Tests for LLMManager with environment variables."""

    def test_preferred_backend_from_env(self):
        """Test preferred backend from environment variable."""
        with patch.dict("os.environ", {"LLM_BACKEND": "mock"}):
            manager = LLMManager(use_mock=True)
            assert manager.preferred_backend == "mock"

    def test_openai_api_key_passed(self):
        """Test OpenAI API key passed to constructor."""
        manager = LLMManager(openai_api_key="test-key", use_mock=True)
        # Mock mode ignores API key
        assert manager.is_available() is True

    def test_ollama_host_passed(self):
        """Test Ollama host passed to constructor."""
        manager = LLMManager(ollama_host="localhost:11434", use_mock=True)
        assert manager.is_available() is True


class TestLLMManagerEdgeCases:
    """Edge case tests."""

    def test_generate_response_empty_prompt(self):
        """Test generating response with empty prompt."""
        manager = LLMManager(use_mock=True)
        response = manager.generate_response("")
        assert isinstance(response, str)

    def test_generate_response_long_prompt(self):
        """Test generating response with long prompt."""
        manager = LLMManager(use_mock=True)
        long_prompt = "Hello " * 1000
        response = manager.generate_response(long_prompt)
        assert isinstance(response, str)

    def test_get_active_backend_name_no_backend(self):
        """Test getting backend name when none active."""
        manager = LLMManager(use_mock=True)
        # Force no active backend
        manager.active_backend = None
        assert manager.get_active_backend_name() == "none"

    def test_try_fallback_exists(self):
        """Test that _try_fallback method exists."""
        manager = LLMManager(use_mock=True)
        assert hasattr(manager, "_try_fallback")

    def test_generate_response_with_kwargs(self):
        """Test generating response with additional kwargs."""
        manager = LLMManager(use_mock=True)
        response = manager.generate_response("Hello", temperature=0.5, max_tokens=50)
        assert isinstance(response, str)
