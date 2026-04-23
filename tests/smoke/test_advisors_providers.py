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
Tests for advisors providers module.

Tests LLM provider implementations and stubs.
"""

import inspect
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.advisors.providers import (
    LLMProvider,
    StubCompletionProvider,
    StubResponsesProvider,
    _build_stub_provider,
    _filter_kwargs_for_callable,
    build_provider_safe,
)


class TestFilterKwargsForCallable:
    """Tests for _filter_kwargs_for_callable function."""

    def test_filters_invalid_kwargs(self):
        """Test that invalid kwargs are filtered."""
        def func(a, b):
            pass
        
        kwargs = {"a": 1, "b": 2, "c": 3}
        result = _filter_kwargs_for_callable(func, kwargs)
        
        assert "c" not in result
        assert result == {"a": 1, "b": 2}

    def test_keeps_all_for_var_kwargs(self):
        """Test that all kwargs kept for **kwargs."""
        def func(a, **kwargs):
            pass
        
        kwargs = {"a": 1, "b": 2, "c": 3}
        result = _filter_kwargs_for_callable(func, kwargs)
        
        assert result == kwargs

    def test_handles_builtin(self):
        """Test handling of builtin functions."""
        kwargs = {"obj": "test"}
        result = _filter_kwargs_for_callable(print, kwargs)
        
        # Should return original or empty, not crash
        assert isinstance(result, dict)


class TestBuildStubProvider:
    """Tests for _build_stub_provider function."""

    def test_builds_completion_provider(self):
        """Test building completion mode provider."""
        config = {"llm_api_mode": "completion"}
        provider = _build_stub_provider(config)
        
        assert isinstance(provider, StubCompletionProvider)
        assert provider.api_mode == "completion"

    def test_builds_responses_provider(self):
        """Test building responses mode provider."""
        config = {"llm_api_mode": "responses"}
        provider = _build_stub_provider(config)
        
        assert isinstance(provider, StubResponsesProvider)
        assert provider.api_mode == "responses"

    def test_defaults_to_completion(self):
        """Test default is completion mode."""
        config = {}
        provider = _build_stub_provider(config)
        
        assert isinstance(provider, StubCompletionProvider)


class TestStubCompletionProvider:
    """Tests for StubCompletionProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = {"model": "test-model"}
        provider = StubCompletionProvider(config)
        
        assert provider.model == "test-model"
        assert provider.api_mode == "completion"

    def test_generate(self):
        """Test generate method."""
        provider = StubCompletionProvider({})
        result = provider.generate("Hello")
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_stream(self):
        """Test generate_stream method."""
        provider = StubCompletionProvider({})
        result = provider.generate_stream("Hello")
        
        assert isinstance(result, str)

    def test_health_check(self):
        """Test health_check method."""
        provider = StubCompletionProvider({})
        result = provider.health_check()
        
        assert result is True


class TestStubResponsesProvider:
    """Tests for StubResponsesProvider."""

    def test_generate(self):
        """Test generate method."""
        provider = StubResponsesProvider({"model": "test", "api_mode": "responses"})
        result = provider.generate("Hello")
        
        assert isinstance(result, str)
        assert "Hello" in result

    def test_generate_stream(self):
        """Test generate_stream method."""
        provider = StubResponsesProvider({"model": "test", "api_mode": "responses"})
        result = provider.generate_stream("Hello")
        
        assert isinstance(result, str)


class TestLLMProviderBase:
    """Tests for LLMProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider({})

    def test_has_abstract_methods(self):
        """Test that abstract methods are defined."""
        assert hasattr(LLMProvider, "generate")
        assert hasattr(LLMProvider, "generate_stream")


class TestBuildProviderSafe:
    """Tests for build_provider_safe function."""

    def test_returns_provider(self):
        """Test that function returns a provider."""
        config = {"llm_api_mode": "completion"}
        provider = build_provider_safe(config)
        
        assert provider is not None
        assert hasattr(provider, "generate")

    def test_handles_completion_mode(self):
        """Test handling of completion mode."""
        config = {"api_mode": "completion"}
        provider = build_provider_safe(config)
        
        assert provider.api_mode == "completion"

    def test_handles_responses_mode(self):
        """Test handling of responses mode."""
        config = {"api_mode": "responses"}
        provider = build_provider_safe(config)
        
        assert provider.api_mode == "responses"


class TestProviderConfiguration:
    """Tests for provider configuration handling."""

    def test_model_parameter(self):
        """Test model parameter extraction."""
        config = {"model": "gpt-4"}
        provider = StubCompletionProvider(config)
        
        assert provider.model == "gpt-4"

    def test_temperature_parameter(self):
        """Test temperature parameter extraction."""
        config = {"temperature": 0.5}
        provider = StubCompletionProvider(config)
        
        assert provider.temperature == 0.5

    def test_max_tokens_parameter(self):
        """Test max_tokens parameter extraction."""
        config = {"max_tokens": 500}
        provider = StubCompletionProvider(config)
        
        assert provider.max_tokens == 500

    def test_api_key_from_config(self):
        """Test API key from config."""
        config = {"api_key": "test-key"}
        provider = StubCompletionProvider(config)
        
        assert provider.api_key == "test-key"

    def test_nested_provider_config(self):
        """Test nested provider configuration."""
        config = {
            "provider": {
                "api_key": "nested-key",
                "base_url": "https://api.example.com",
            }
        }
        provider = StubCompletionProvider(config)
        
        assert provider.api_key == "nested-key"
        assert provider.base_url == "https://api.example.com"

    def test_default_values(self):
        """Test default parameter values."""
        provider = StubCompletionProvider({})
        
        assert provider.model == "gpt-3.5-turbo"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 1000
        assert provider.max_retries == 3
        assert provider.timeout == 30


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_config(self):
        """Test with empty config."""
        provider = StubCompletionProvider({})
        
        result = provider.generate("Test")
        assert isinstance(result, str)

    def test_none_config_values(self):
        """Test handling of None config values."""
        config = {
            "model": None,
            "api_key": None,
        }
        provider = StubCompletionProvider(config)
        
        # Should use defaults or handle None
        assert provider.model is None or provider.model == "gpt-3.5-turbo"

    def test_generate_with_empty_prompt(self):
        """Test generate with empty prompt."""
        provider = StubCompletionProvider({})
        
        result = provider.generate("")
        assert isinstance(result, str)

    def test_generate_with_long_prompt(self):
        """Test generate with very long prompt."""
        provider = StubCompletionProvider({})
        long_prompt = "test " * 1000
        
        result = provider.generate(long_prompt)
        assert isinstance(result, str)
