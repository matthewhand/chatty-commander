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
Comprehensive tests for Ollama provider module.

Tests Ollama API integration, request handling, and streaming.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from src.chatty_commander.providers.ollama_provider import OllamaProvider


class TestOllamaProviderInitialization:
    """Tests for OllamaProvider initialization."""

    def test_default_initialization(self):
        """Test initialization with default config."""
        provider = OllamaProvider({})
        
        assert provider.ollama_host == "http://localhost:11434"
        assert provider.model == "gpt-oss:20b"
        assert provider.base_url == "http://localhost:11434/api"

    def test_custom_host(self):
        """Test initialization with custom host."""
        provider = OllamaProvider({"ollama_host": "http://192.168.1.100:11434"})
        
        assert provider.ollama_host == "http://192.168.1.100:11434"
        assert provider.base_url == "http://192.168.1.100:11434/api"

    def test_custom_model(self):
        """Test initialization with custom model."""
        provider = OllamaProvider({"model": "llama2:7b"})
        
        assert provider.model == "llama2:7b"

    def test_stream_setting(self):
        """Test stream configuration."""
        provider = OllamaProvider({"stream": True})
        
        assert provider.stream is True

    def test_keep_alive_setting(self):
        """Test keep_alive configuration."""
        provider = OllamaProvider({"keep_alive": "10m"})
        
        assert provider.keep_alive == "10m"

    def test_num_ctx_setting(self):
        """Test num_ctx configuration."""
        provider = OllamaProvider({"num_ctx": 4096})
        
        assert provider.num_ctx == 4096

    def test_session_headers(self):
        """Test that session headers are set correctly."""
        provider = OllamaProvider({})
        
        assert provider.session.headers["Content-Type"] == "application/json"
        assert "User-Agent" in provider.session.headers
        assert "chatty-commander" in provider.session.headers["User-Agent"]


class TestMakeRequest:
    """Tests for _make_request method."""

    @pytest.fixture
    def provider(self):
        """Create OllamaProvider instance."""
        return OllamaProvider({})

    def test_successful_request(self, provider):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response):
            response = provider._make_request("generate", {"prompt": "test"})
            
            assert response is mock_response

    def test_request_with_correct_url(self, provider):
        """Test that request uses correct URL."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response) as mock_post:
            provider._make_request("generate", {"prompt": "test"})
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "http://localhost:11434/api/generate" in str(call_args)

    def test_request_timeout(self, provider):
        """Test that request uses timeout."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response) as mock_post:
            provider._make_request("generate", {"prompt": "test"})
            
            _, kwargs = mock_post.call_args
            assert "timeout" in kwargs

    def test_request_retries_on_failure(self, provider):
        """Test that failed requests are retried."""
        with patch.object(provider.session, 'post') as mock_post:
            # First two calls fail, third succeeds
            mock_post.side_effect = [
                requests.RequestException("Connection error"),
                requests.RequestException("Connection error"),
                Mock(raise_for_status=lambda: None)
            ]
            
            with patch('time.sleep'):  # Skip sleep for faster tests
                response = provider._make_request("generate", {"prompt": "test"})
                
                assert mock_post.call_count == 3
                assert response is not None

    def test_exhausted_retries_raises_error(self, provider):
        """Test that exhausted retries raise RuntimeError."""
        with patch.object(provider.session, 'post') as mock_post:
            mock_post.side_effect = requests.RequestException("Always fails")
            
            with patch('time.sleep'):
                with pytest.raises(RuntimeError) as exc_info:
                    provider._make_request("generate", {"prompt": "test"})
                
                assert "Failed to connect to Ollama" in str(exc_info.value)


class TestGenerate:
    """Tests for generate method."""

    @pytest.fixture
    def provider(self):
        """Create OllamaProvider instance."""
        return OllamaProvider({})

    def test_successful_generation(self, provider):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello, world!"}
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            result = provider.generate("Say hello")
            
            assert result == "Hello, world!"

    def test_generation_strips_whitespace(self, provider):
        """Test that generated text is stripped."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "  Trimmed  "}
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            result = provider.generate("Test")
            
            assert result == "Trimmed"

    def test_missing_response_field(self, provider):
        """Test handling of missing response field."""
        mock_response = Mock()
        mock_response.json.return_value = {"other": "data"}
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            result = provider.generate("Test")
            
            assert "Error" in result
            assert "Invalid response" in result

    def test_request_exception_handling(self, provider):
        """Test handling of request exceptions."""
        with patch.object(provider, '_make_request', side_effect=Exception("Network error")):
            result = provider.generate("Test")
            
            assert "Error" in result
            assert "Failed to generate" in result

    def test_payload_includes_correct_options(self, provider):
        """Test that payload includes correct generation options."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Test"}
        
        with patch.object(provider, '_make_request') as mock_make_request:
            mock_make_request.return_value = mock_response
            
            provider.generate("Prompt", temperature=0.8, top_p=0.9, num_ctx=4096)
            
            call_args = mock_make_request.call_args
            payload = call_args[0][1]
            
            assert payload["model"] == provider.model
            assert payload["prompt"] == "Prompt"
            assert payload["options"]["temperature"] == 0.8
            assert payload["options"]["top_p"] == 0.9
            assert payload["options"]["num_ctx"] == 4096


class TestGenerateStream:
    """Tests for generate_stream method."""

    @pytest.fixture
    def provider(self):
        """Create OllamaProvider instance."""
        return OllamaProvider({})

    def test_streaming_generation(self, provider):
        """Test streaming text generation."""
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"response": "Hello"}',
            b'{"response": " world"}',
            b'{"response": "!", "done": true}',
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response):
            chunks = list(provider.generate_stream("Say hello"))
            
            assert chunks == ["Hello", " world", "!"]

    def test_streaming_handles_json_decode_errors(self, provider):
        """Test that JSON decode errors are handled gracefully."""
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"response": "Valid"}',
            b'Invalid JSON',
            b'{"response": "Still works"}',
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response):
            chunks = list(provider.generate_stream("Test"))
            
            assert "Valid" in chunks
            assert "Still works" in chunks

    def test_streaming_request_exception(self, provider):
        """Test handling of streaming request exceptions."""
        with patch.object(provider.session, 'post', side_effect=Exception("Connection lost")):
            chunks = list(provider.generate_stream("Test"))
            
            assert len(chunks) == 1
            assert "Error" in chunks[0]

    def test_streaming_uses_correct_endpoint(self, provider):
        """Test that streaming uses correct endpoint."""
        mock_response = Mock()
        mock_response.iter_lines.return_value = []
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            list(provider.generate_stream("Test"))
            
            call_args = mock_post.call_args
            assert "http://localhost:11434/api/generate" in str(call_args)
            assert call_args[1]["stream"] is True


class TestHealthCheck:
    """Tests for health_check method."""

    @pytest.fixture
    def provider(self):
        """Create OllamaProvider instance."""
        return OllamaProvider({})

    def test_healthy_when_model_available(self, provider):
        """Test health check when model is available."""
        provider.model = "gpt-oss:20b"
        
        # Mock the tags response
        mock_tags_response = Mock()
        mock_tags_response.json.return_value = {
            "models": [{"name": "gpt-oss:20b"}]
        }
        mock_tags_response.raise_for_status.return_value = None
        
        # Mock the generate call within health_check
        with patch.object(provider.session, 'get', return_value=mock_tags_response):
            with patch.object(provider, 'generate', return_value="Hello response"):
                result = provider.health_check()
                
                assert result is True

    def test_unhealthy_when_model_missing(self, provider):
        """Test health check when model is not available."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [{"name": "other-model"}]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'get', return_value=mock_response):
            result = provider.health_check()
            
            assert result is False

    def test_unhealthy_when_request_fails(self, provider):
        """Test health check when request fails."""
        with patch.object(provider.session, 'get', side_effect=Exception("Connection error")):
            result = provider.health_check()
            
            assert result is False

    def test_healthy_with_multiple_models(self, provider):
        """Test health check with multiple models."""
        provider.model = "gpt-oss:20b"
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:7b"},
                {"name": "gpt-oss:20b"},
                {"name": "mistral"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'get', return_value=mock_response):
            result = provider.health_check()
            
            assert result is True


class TestOllamaProviderEdgeCases:
    """Edge case tests."""

    def test_generate_with_empty_prompt(self):
        """Test generation with empty prompt."""
        provider = OllamaProvider({})
        mock_response = Mock()
        mock_response.json.return_value = {"response": "OK"}
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            result = provider.generate("")
            
            assert result == "OK"

    def test_generate_with_long_prompt(self):
        """Test generation with very long prompt."""
        provider = OllamaProvider({})
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        
        long_prompt = "x" * 10000
        
        with patch.object(provider, '_make_request', return_value=mock_response) as mock_make:
            provider.generate(long_prompt)
            
            call_args = mock_make.call_args
            assert call_args[0][1]["prompt"] == long_prompt

    def test_stream_with_special_characters(self):
        """Test streaming with special characters in response."""
        provider = OllamaProvider({})
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            json.dumps({"response": "Hello \"world\""}).encode(),
            json.dumps({"response": "Special: <>&"}).encode(),
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch.object(provider.session, 'post', return_value=mock_response):
            chunks = list(provider.generate_stream("Test"))
            
            assert 'Hello "world"' in chunks
            assert "Special: <>&" in chunks
