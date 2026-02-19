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

"""Additional tests to improve coverage for llm/backends.py."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestOpenAIBackend:
    """Tests for OpenAIBackend class."""

    def test_init_without_api_key(self):
        """Test OpenAIBackend initialization without API key."""
        from chatty_commander.llm.backends import OpenAIBackend

        with patch.dict(os.environ, {}, clear=True):
            backend = OpenAIBackend()

        assert backend.api_key is None
        assert backend._client is None

    def test_init_with_api_key(self):
        """Test OpenAIBackend initialization with API key."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key")

        assert backend.api_key == "test-key"
        assert backend._client == mock_client

    def test_init_with_custom_base_url(self):
        """Test OpenAIBackend initialization with custom base URL."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client) as mock_openai:
                backend = OpenAIBackend(api_key="test-key", base_url="https://custom.api.com/v1")

        assert backend.base_url == "https://custom.api.com/v1"
        mock_openai.assert_called_once()

    def test_init_with_custom_timeout_and_retries(self):
        """Test OpenAIBackend initialization with custom timeout and retries."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(
                    api_key="test-key",
                    timeout=60.0,
                    max_retries=5,
                )

        assert backend.timeout == 60.0
        assert backend.max_retries == 5

    def test_init_import_error(self):
        """Test OpenAIBackend handles ImportError gracefully."""
        from chatty_commander.llm.backends import OpenAIBackend

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.dict(
                "sys.modules",
                {"openai": None, "openai.OpenAI": None},
            ):
                # Force re-import to trigger ImportError path
                import importlib
                import chatty_commander.llm.backends as backends_mod
                importlib.reload(backends_mod)

                # After reload, get the class again
                OpenAIBackend = backends_mod.OpenAIBackend
                backend = OpenAIBackend(api_key="test-key")

                assert backend._client is None

    def test_is_available_no_client(self):
        """Test is_available returns False when no client."""
        from chatty_commander.llm.backends import OpenAIBackend

        backend = OpenAIBackend()
        assert backend.is_available() is False

    def test_is_available_with_client_success(self):
        """Test is_available returns True when client works."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key")
                backend._client = mock_client

        assert backend.is_available() is True

    def test_is_available_with_client_failure(self):
        """Test is_available returns False when client fails."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key")
                backend._client = mock_client

        assert backend.is_available() is False

    def test_generate_response_no_client(self):
        """Test generate_response raises error when no client."""
        from chatty_commander.llm.backends import OpenAIBackend

        backend = OpenAIBackend()
        # Ensure client is None
        backend._client = None

        with pytest.raises(RuntimeError, match="not available"):
            backend.generate_response("test prompt")

    def test_generate_response_success(self):
        """Test generate_response returns response."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  Test response  "
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key")
                backend._client = mock_client

        result = backend.generate_response("test prompt")
        assert result == "Test response"

    def test_generate_response_with_custom_params(self):
        """Test generate_response passes custom parameters."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key")
                backend._client = mock_client

        result = backend.generate_response(
            "test prompt",
            model="gpt-4",
            max_tokens=500,
            temperature=0.5,
        )

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["temperature"] == 0.5

    def test_generate_response_retry_success(self):
        """Test generate_response retries on failure then succeeds."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"

        # Fail first time, succeed second time
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary error"),
            mock_response,
        ]

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key", max_retries=2)
                backend._client = mock_client

        with patch("time.sleep"):  # Skip actual sleep
            result = backend.generate_response("test prompt")

        assert result == "Success"
        assert mock_client.chat.completions.create.call_count == 2

    def test_generate_response_all_retries_fail(self):
        """Test generate_response raises after all retries fail."""
        from chatty_commander.llm.backends import OpenAIBackend

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Persistent error")

        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI", return_value=mock_client):
                backend = OpenAIBackend(api_key="test-key", max_retries=2)
                backend._client = mock_client

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="failed after"):
                backend.generate_response("test prompt")

    def test_get_backend_info(self):
        """Test get_backend_info returns correct info."""
        from chatty_commander.llm.backends import OpenAIBackend

        with patch.dict(os.environ, {}, clear=True):
            backend = OpenAIBackend(api_key="test-key", base_url="https://custom.api.com")

        info = backend.get_backend_info()

        assert info["backend"] == "openai"
        assert "available" in info
        assert info["base_url"] == "https://custom.api.com"
        assert info["has_api_key"] is True
        assert info["max_retries"] == 3


class TestOllamaBackend:
    """Tests for OllamaBackend class."""

    def test_init_default_values(self):
        """Test OllamaBackend initialization with defaults."""
        from chatty_commander.llm.backends import OllamaBackend

        with patch.dict(os.environ, {}, clear=True):
            backend = OllamaBackend()

        assert backend.host == "ollama:11434"
        assert backend.model == "gpt-oss:20b"
        assert backend.base_url == "http://ollama:11434"

    def test_init_custom_values(self):
        """Test OllamaBackend initialization with custom values."""
        from chatty_commander.llm.backends import OllamaBackend

        with patch.dict(os.environ, {}, clear=True):
            backend = OllamaBackend(host="localhost:11434", model="llama2")

        assert backend.host == "localhost:11434"
        assert backend.model == "llama2"

    def test_init_from_env(self):
        """Test OllamaBackend reads from environment."""
        from chatty_commander.llm.backends import OllamaBackend

        with patch.dict(os.environ, {"OLLAMA_HOST": "custom-host:1234"}):
            backend = OllamaBackend()

        assert backend.host == "custom-host:1234"

    def test_is_available_cached_true(self):
        """Test is_available returns cached True value."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend()
        backend._available = True

        assert backend.is_available() is True

    def test_is_available_cached_false(self):
        """Test is_available returns cached False value."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend()
        backend._available = False

        assert backend.is_available() is False

    def test_is_available_server_responding_model_found(self):
        """Test is_available when server responds and model is found."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama2"}]}

        with patch("requests.get", return_value=mock_response):
            backend = OllamaBackend(model="llama2")
            result = backend.is_available()

        assert result is True

    def test_is_available_server_responding_model_not_found(self):
        """Test is_available when server responds but model not found."""
        from chatty_commander.llm.backends import OllamaBackend

        # First response: model not found
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other-model"}]}

        # Pull response
        mock_pull_response = MagicMock()
        mock_pull_response.status_code = 200

        # After pull, model is available
        mock_tags_after_pull = MagicMock()
        mock_tags_after_pull.json.return_value = {"models": [{"name": "llama2"}]}

        call_count = [0]
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response
            return mock_tags_after_pull

        with patch("requests.get", side_effect=get_side_effect):
            with patch("requests.post", return_value=mock_pull_response):
                backend = OllamaBackend(model="llama2")
                result = backend.is_available()

        # Should try to pull and succeed
        assert result is True

    def test_is_available_server_not_responding(self):
        """Test is_available when server doesn't respond."""
        from chatty_commander.llm.backends import OllamaBackend

        with patch("requests.get", side_effect=Exception("Connection error")):
            backend = OllamaBackend()
            result = backend.is_available()

        assert result is False

    def test_is_available_non_200_status(self):
        """Test is_available when server returns non-200 status."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.get", return_value=mock_response):
            backend = OllamaBackend()
            result = backend.is_available()

        assert result is False

    def test_is_available_import_error(self):
        """Test is_available handles ImportError."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend()

        with patch.dict("sys.modules", {"requests": None}):
            result = backend.is_available()

        assert result is False

    def test_try_pull_model_success(self):
        """Test _try_pull_model succeeds."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response):
            backend = OllamaBackend(model="llama2")
            backend._try_pull_model()

    def test_try_pull_model_failure(self):
        """Test _try_pull_model handles failure."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.post", return_value=mock_response):
            backend = OllamaBackend(model="llama2")
            backend._try_pull_model()  # Should not raise

    def test_try_pull_model_exception(self):
        """Test _try_pull_model handles exception."""
        from chatty_commander.llm.backends import OllamaBackend

        with patch("requests.post", side_effect=Exception("Network error")):
            backend = OllamaBackend(model="llama2")
            backend._try_pull_model()  # Should not raise

    def test_generate_response_not_available(self):
        """Test generate_response raises when not available."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend()
        backend._available = False

        with pytest.raises(RuntimeError, match="not available"):
            backend.generate_response("test prompt")

    def test_generate_response_success(self):
        """Test generate_response returns response."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "  Test response  "}

        backend = OllamaBackend()
        backend._available = True

        with patch("requests.post", return_value=mock_response):
            result = backend.generate_response("test prompt")

        assert result == "Test response"

    def test_generate_response_with_custom_params(self):
        """Test generate_response passes custom parameters."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Response"}

        backend = OllamaBackend()
        backend._available = True

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = backend.generate_response(
                "test prompt",
                max_tokens=500,
                temperature=0.5,
            )

        call_kwargs = mock_post.call_args[1]["json"]
        assert call_kwargs["options"]["num_predict"] == 500
        assert call_kwargs["options"]["temperature"] == 0.5

    def test_generate_response_failure(self):
        """Test generate_response handles failure."""
        from chatty_commander.llm.backends import OllamaBackend

        mock_response = MagicMock()
        mock_response.status_code = 500

        backend = OllamaBackend()
        backend._available = True

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="request failed"):
                backend.generate_response("test prompt")

    def test_generate_response_exception(self):
        """Test generate_response handles exception."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend()
        backend._available = True

        with patch("requests.post", side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                backend.generate_response("test prompt")

    def test_get_backend_info(self):
        """Test get_backend_info returns correct info."""
        from chatty_commander.llm.backends import OllamaBackend

        backend = OllamaBackend(host="localhost:11434", model="llama2")
        info = backend.get_backend_info()

        assert info["backend"] == "ollama"
        assert "available" in info
        assert info["host"] == "localhost:11434"
        assert info["model"] == "llama2"


class TestLocalTransformersBackend:
    """Tests for LocalTransformersBackend class."""

    def test_init_import_error(self):
        """Test LocalTransformersBackend handles ImportError."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        with patch.dict("sys.modules", {"torch": None, "transformers": None}):
            backend = LocalTransformersBackend()

        assert backend._model is None
        assert backend._tokenizer is None

    def test_is_available_no_model(self):
        """Test is_available returns False when no model loaded."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend()
        assert backend.is_available() is False

    def test_is_available_with_model(self):
        """Test is_available returns True when model loaded."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend()
        backend._model = MagicMock()
        backend._tokenizer = MagicMock()

        assert backend.is_available() is True

    def test_generate_response_not_available(self):
        """Test generate_response raises when not available."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend()

        with pytest.raises(RuntimeError, match="not available"):
            backend.generate_response("test prompt")

    def test_generate_response_success(self):
        """Test generate_response returns response."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend()
        backend._model = MagicMock()
        backend._tokenizer = MagicMock()
        backend._device = "cpu"

        # Mock tokenizer encoding
        mock_inputs = MagicMock()
        mock_inputs.shape = [1, 5]
        mock_inputs.__getitem__ = lambda self, idx: 5  # For inputs.shape[1]
        backend._tokenizer.encode.return_value.to.return_value = mock_inputs
        backend._tokenizer.eos_token_id = 1
        backend._tokenizer.decode.return_value = "  Test response  "

        # Mock model generation - return tensor-like output
        mock_outputs = MagicMock()
        mock_outputs.__getitem__ = lambda self, idx: MagicMock()
        # Make the sliced output iterable for decode
        mock_outputs[0].__getitem__ = lambda self, idx: [0, 0, 0]
        backend._model.generate.return_value = mock_outputs

        # Mock torch operations
        mock_torch = MagicMock()
        mock_torch.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_torch.ones_like = MagicMock(return_value=MagicMock())

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = backend.generate_response("test prompt")

        assert result == "Test response"

    def test_generate_response_exception(self):
        """Test generate_response handles exception."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend()
        backend._model = MagicMock()
        backend._tokenizer = MagicMock()
        backend._device = "cpu"

        backend._tokenizer.encode.side_effect = Exception("Encoding error")

        mock_torch = MagicMock()
        mock_torch.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))

        with patch.dict("sys.modules", {"torch": mock_torch}):
            with pytest.raises(Exception, match="Encoding error"):
                backend.generate_response("test prompt")

    def test_get_backend_info(self):
        """Test get_backend_info returns correct info."""
        from chatty_commander.llm.backends import LocalTransformersBackend

        backend = LocalTransformersBackend(model_name="test-model")
        backend._device = "cpu"

        info = backend.get_backend_info()

        assert info["backend"] == "local_transformers"
        assert "available" in info
        assert info["model_name"] == "test-model"
        assert info["device"] == "cpu"


class TestMockLLMBackend:
    """Tests for MockLLMBackend class."""

    def test_init_default_responses(self):
        """Test MockLLMBackend initialization with defaults."""
        from chatty_commander.llm.backends import MockLLMBackend

        backend = MockLLMBackend()

        assert len(backend.responses) == 5
        assert backend.call_count == 0

    def test_init_custom_responses(self):
        """Test MockLLMBackend initialization with custom responses."""
        from chatty_commander.llm.backends import MockLLMBackend

        backend = MockLLMBackend(responses=["Response 1", "Response 2"])

        assert len(backend.responses) == 2

    def test_is_available(self):
        """Test MockLLMBackend is always available."""
        from chatty_commander.llm.backends import MockLLMBackend

        backend = MockLLMBackend()
        assert backend.is_available() is True

    def test_generate_response_cycles(self):
        """Test MockLLMBackend cycles through responses."""
        from chatty_commander.llm.backends import MockLLMBackend

        backend = MockLLMBackend(responses=["A", "B"])

        assert backend.generate_response("prompt") == "A"
        assert backend.generate_response("prompt") == "B"
        assert backend.generate_response("prompt") == "A"  # Cycles back

    def test_get_backend_info(self):
        """Test get_backend_info returns correct info."""
        from chatty_commander.llm.backends import MockLLMBackend

        backend = MockLLMBackend(responses=["A", "B"])
        backend.call_count = 3

        info = backend.get_backend_info()

        assert info["backend"] == "mock"
        assert info["available"] is True
        assert info["responses_count"] == 2
        assert info["call_count"] == 3


class TestLLMBackendABC:
    """Tests for LLMBackend abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test LLMBackend cannot be instantiated directly."""
        from chatty_commander.llm.backends import LLMBackend

        with pytest.raises(TypeError):
            LLMBackend()

    def test_subclass_must_implement_methods(self):
        """Test subclass must implement all abstract methods."""
        from chatty_commander.llm.backends import LLMBackend

        class IncompleteBackend(LLMBackend):
            pass

        with pytest.raises(TypeError):
            IncompleteBackend()
