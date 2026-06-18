"""Unit tests for llm/backends.py .

Covers ABC, MockLLMBackend (primary for fast unit), and construction of others under patch.
Uses AAA, patches for heavy optional deps (openai, httpx, torch, transformers).
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.llm.backends import (
    LLMBackend,
    LocalTransformersBackend,
    MockLLMBackend,
    OllamaBackend,
    OpenAIBackend,
)

# ============================================================================
# MOCK BACKEND (always available, deterministic for unit)
# ============================================================================


class TestMockLLMBackend:
    """MockLLMBackend - the reliable test backend."""

    def test_mock_always_available(self):
        # Arrange
        mb = MockLLMBackend()
        # Act / Assert
        assert mb.is_available() is True
        assert mb.call_count == 0

    def test_mock_generate_cycles_responses(self):
        # Arrange
        mb = MockLLMBackend(responses=["r0", "r1"])
        # Act
        r1 = mb.generate_response("p1")
        r2 = mb.generate_response("p2")
        r3 = mb.generate_response("p3")
        # Assert
        assert r1 == "r0"
        assert r2 == "r1"
        assert r3 == "r0"  # cycled
        assert mb.call_count == 3
        info = mb.get_backend_info()
        assert info["backend"] == "mock"
        assert info["call_count"] == 3

    def test_mock_get_info(self):
        # Arrange
        mb = MockLLMBackend()
        # Act
        info = mb.get_backend_info()
        # Assert
        assert "responses_count" in info
        assert info["available"] is True


# ============================================================================
# ABSTRACT + CONCRETE CONSTRUCTORS (under patches)
# ============================================================================


class TestLLMBackendABCAndOthers:
    """Construction and info for real backends (no network/ heavy init)."""

    def test_llm_backend_is_abstract(self):
        # Act / Assert
        with pytest.raises(TypeError):
            LLMBackend()  # type: ignore[abstract]

    def test_openai_backend_init_without_key(self):
        # Arrange / Act - no key -> no client
        with patch.dict("os.environ", {}, clear=True):
            ob = OpenAIBackend(api_key=None)
        # Assert
        assert ob.api_key is None or ob.api_key == ""
        assert ob._client is None
        assert ob.is_available() is False
        info = ob.get_backend_info()
        assert info["backend"] == "openai"
        assert info["has_api_key"] is False

    def test_openai_backend_generate_raises_without_client(self):
        ob = OpenAIBackend(api_key=None)
        with pytest.raises(RuntimeError, match="not available"):
            ob.generate_response("prompt")

    def test_ollama_backend_constructs_and_info(self):
        # Arrange / Act
        ob = OllamaBackend(host="localhost:11434", model="test-model")
        # Assert
        assert "http://" in ob.base_url
        assert "localhost" in ob.base_url
        info = ob.get_backend_info()
        assert info["backend"] == "ollama"
        assert info["model"] == "test-model"
        # is_available will be False without httpx/real server but exercised
        assert isinstance(ob.is_available(), bool)

    def test_local_transformers_constructs_without_deps(self):
        # Arrange
        with patch.dict("sys.modules", {"torch": None, "transformers": None}):
            with patch("builtins.__import__", side_effect=ImportError("no torch")):
                # Act - should not crash hard, just warn
                lb = LocalTransformersBackend(model_name="dummy")
        # Assert
        assert lb.is_available() is False  # because init failed gracefully
        info = lb.get_backend_info()
        assert info["backend"] == "local_transformers"


# ============================================================================
# ERROR / EDGE PATHS (via patches on internals)
# ============================================================================


class TestBackendsErrorPaths:
    """Graceful degradation and error paths."""

    def test_mock_handles_prompt(self):
        # Arrange
        mb = MockLLMBackend()
        # Act
        out = mb.generate_response("")
        # Assert
        assert isinstance(out, str)

    def test_ollama_is_available_false_on_import_error(self):
        # Arrange
        ob = OllamaBackend()
        with patch("builtins.__import__", side_effect=ImportError("no httpx")):
            # Act
            avail = ob.is_available()
        # Assert
        assert avail is False

    def test_openai_retries_and_raises(self):
        # Arrange
        ob = OpenAIBackend(api_key="fake")
        ob._client = Mock()
        ob._client.chat.completions.create.side_effect = Exception("api fail")
        # Act / Assert
        with pytest.raises(RuntimeError, match="failed after"):
            ob.generate_response("p", max_tokens=5)
