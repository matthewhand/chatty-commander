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

"""Tests for LLM backends module."""

from unittest.mock import MagicMock, patch

import pytest

from src.chatty_commander.llm.backends import LLMBackend, OpenAIBackend, OllamaBackend


class TestLLMBackend:
    """Tests for LLMBackend abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that LLMBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMBackend()


class TestOpenAIBackend:
    """Tests for OpenAIBackend."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            backend = OpenAIBackend()
            assert backend.api_key is None
            assert backend._client is None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        backend = OpenAIBackend(api_key="test-key")
        assert backend.api_key == "test-key"

    def test_default_base_url(self):
        """Test default base URL."""
        with patch.dict("os.environ", {}, clear=True):
            backend = OpenAIBackend()
            assert "api.openai.com" in backend.base_url

    def test_custom_base_url(self):
        """Test custom base URL."""
        backend = OpenAIBackend(base_url="https://custom.api.com")
        assert backend.base_url == "https://custom.api.com"

    def test_is_available_without_client(self):
        """Test availability without client."""
        with patch.dict("os.environ", {}, clear=True):
            backend = OpenAIBackend()
            assert backend.is_available() is False

    def test_get_backend_info(self):
        """Test getting backend info."""
        backend = OpenAIBackend(api_key="test-key")
        info = backend.get_backend_info()
        assert "backend" in info
        assert info["backend"] == "openai"
        assert "has_api_key" in info
        assert info["has_api_key"] is True

    def test_default_retries(self):
        """Test default retry count."""
        backend = OpenAIBackend()
        assert backend.max_retries == 3

    def test_custom_retries(self):
        """Test custom retry count."""
        backend = OpenAIBackend(max_retries=5)
        assert backend.max_retries == 5

    def test_default_timeout(self):
        """Test default timeout."""
        backend = OpenAIBackend()
        assert backend.timeout == 30.0

    def test_custom_timeout(self):
        """Test custom timeout."""
        backend = OpenAIBackend(timeout=60.0)
        assert backend.timeout == 60.0


class TestOllamaBackend:
    """Tests for OllamaBackend."""

    def test_default_host(self):
        """Test default host configuration."""
        with patch.dict("os.environ", {}, clear=True):
            backend = OllamaBackend()
            assert backend.host == "ollama:11434"

    def test_custom_host(self):
        """Test custom host configuration."""
        backend = OllamaBackend(host="localhost:11434")
        assert backend.host == "localhost:11434"

    def test_default_model(self):
        """Test default model."""
        backend = OllamaBackend()
        assert backend.model == "gpt-oss:20b"

    def test_custom_model(self):
        """Test custom model."""
        backend = OllamaBackend(model="llama2:7b")
        assert backend.model == "llama2:7b"

    def test_base_url_construction(self):
        """Test base URL is constructed correctly."""
        backend = OllamaBackend(host="localhost:11434")
        assert backend.base_url == "http://localhost:11434"

    def test_get_backend_info_unavailable(self):
        """Test getting backend info when not available."""
        backend = OllamaBackend()
        info = backend.get_backend_info()
        assert "backend" in info
        assert info["backend"] == "ollama"
        assert "available" in info
        assert "host" in info
        assert "model" in info


class TestBackendEdgeCases:
    """Edge case tests for backends."""

    def test_openai_empty_api_key(self):
        """Test OpenAI backend with empty API key string."""
        backend = OpenAIBackend(api_key="")
        # Empty string is falsy, so api_key may be None from env fallback
        assert backend.api_key == "" or backend.api_key is None

    def test_ollama_env_host(self):
        """Test Ollama backend with environment variable host."""
        with patch.dict("os.environ", {"OLLAMA_HOST": "custom:11434"}):
            backend = OllamaBackend()
            assert backend.host == "custom:11434"
