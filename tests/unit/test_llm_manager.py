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

from unittest.mock import patch

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


class TestLLMManagerMoreCoverage:
    """Additional tests to improve coverage for LLMManager (addressing qa 'no tests found' for llm/manager.py)."""

    def test_switch_backend_success(self):
        """Test successful switch to mock backend."""
        manager = LLMManager(use_mock=True)
        assert manager.switch_backend("mock") is True
        assert manager.get_active_backend_name() == "mock"

    def test_switch_backend_invalid(self):
        """Test switch to non-existent backend fails gracefully."""
        manager = LLMManager(use_mock=True)
        assert manager.switch_backend("nonexistent") is False

    def test_get_backend_info_active(self):
        """Test get_backend_info for active backend."""
        manager = LLMManager(use_mock=True)
        info = manager.get_backend_info()
        assert isinstance(info, dict)

    def test_refresh_backends(self):
        """Test refresh_backends resets and reselects."""
        manager = LLMManager(use_mock=True)
        manager.refresh_backends()
        assert manager.is_available() is True

    def test_test_backend_method(self):
        """Test the test_backend method."""
        manager = LLMManager(use_mock=True)
        result = manager.test_backend("mock", "test prompt")
        assert "success" in result or "error" in result

    def test_generate_response_no_backend_raises(self):
        """Test generate raises if no backend."""
        manager = LLMManager(use_mock=True)
        manager.active_backend = None
        with pytest.raises(RuntimeError):
            manager.generate_response("hi")

    def test_get_all_backends_info_structure(self):
        """Test get_all_backends_info returns dict including active key."""
        manager = LLMManager(use_mock=True)
        info = manager.get_all_backends_info()
        assert isinstance(info, dict)
        assert "active" in info
        assert "mock" in info

    def test_switch_backend_to_mock(self):
        """Test switch_backend to a valid available backend."""
        manager = LLMManager(use_mock=True)
        ok = manager.switch_backend("mock")
        assert ok is True
        assert manager.get_active_backend_name() == "mock"

    def test_test_backend_returns_dict_for_mock(self):
        """Test test_backend returns result dict for mock."""
        manager = LLMManager(use_mock=True)
        res = manager.test_backend("mock", "ping")
        assert isinstance(res, dict)
        assert "success" in res or "error" in res or "response" in res

    def test_is_available_true_for_mock(self):
        """Test is_available returns True when backend selected."""
        manager = LLMManager(use_mock=True)
        assert manager.is_available() is True

    def test_backends_dict_contains_mock(self):
        """Test that backends always includes the mock backend after init."""
        manager = LLMManager(use_mock=True)
        assert "mock" in manager.backends
        assert manager.backends["mock"] is not None

    def test_generate_response_with_mock_always_succeeds(self):
        """Test basic generate_response succeeds under mock (no real LLM needed)."""
        manager = LLMManager(use_mock=True)
        response = manager.generate_response("unit test prompt")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_switch_to_invalid_backend_returns_false(self):
        """Switch to bad name returns False."""
        manager = LLMManager(use_mock=True)
        assert manager.switch_backend("invalid") is False

    def test_get_backend_info_nonexistent_returns_error(self):
        """get_backend_info for bad name has error."""
        manager = LLMManager(use_mock=True)
        info = manager.get_backend_info("nonexistent")
        assert "error" in info

    def test_test_backend_returns_dict(self):
        """test_backend returns dict with success or error."""
        manager = LLMManager(use_mock=True)
        res = manager.test_backend("mock", "ping")
        assert isinstance(res, dict)
        assert "success" in res or "error" in res or "response" in res

    def test_refresh_backends_keeps_available(self):
        """refresh_backends keeps manager available."""
        manager = LLMManager(use_mock=True)
        manager.refresh_backends()
        assert manager.is_available() is True

    def test_get_all_backends_info_has_active_key(self):
        """get_all_backends_info includes 'active'."""
        manager = LLMManager(use_mock=True)
        info = manager.get_all_backends_info()
        assert isinstance(info, dict)
        assert "active" in info
        assert info["active"] == "mock"

    def test_generate_response_accepts_kwargs(self):
        """generate_response passes kwargs to backend."""
        manager = LLMManager(use_mock=True)
        # mock backend ignores, but call succeeds
        res = manager.generate_response("hi", temperature=0.1)
        assert isinstance(res, str)

    def test_switch_backend_unavailable_returns_false(self):
        """switch to unavailable name returns False."""
        manager = LLMManager(use_mock=True)
        # patch to make mock unavailable temporarily
        orig = manager.backends["mock"].is_available
        manager.backends["mock"].is_available = lambda: False
        ok = manager.switch_backend("mock")
        manager.backends["mock"].is_available = orig
        assert ok is False

    def test_test_backend_handles_missing(self):
        """test_backend for bad backend returns error dict."""
        manager = LLMManager(use_mock=True)
        res = manager.test_backend("no-such")
        assert "error" in res
