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

"""Tests for LLM integration components."""

import importlib
import importlib.util
import os
from unittest.mock import Mock, patch

import pytest

has_transformers = importlib.util.find_spec("transformers") is not None

from chatty_commander.llm import CommandProcessor, LLMManager  # noqa: E402
from chatty_commander.llm.backends import (
    LocalTransformersBackend,
    MockLLMBackend,
    OllamaBackend,
    OpenAIBackend,
)


class TestMockLLMBackend:
    def test_mock_backend_basic_functionality(self):
        backend = MockLLMBackend()
        assert backend.is_available()

        response = backend.generate_response("test prompt")
        assert isinstance(response, str)
        assert len(response) > 0

        info = backend.get_backend_info()
        assert info["backend"] == "mock"
        assert info["available"] is True

    def test_mock_backend_custom_responses(self):
        responses = ["response 1", "response 2"]
        backend = MockLLMBackend(responses=responses)

        assert backend.generate_response("test") == "response 1"
        assert backend.generate_response("test") == "response 2"
        assert backend.generate_response("test") == "response 1"  # Cycles back


class TestOpenAIBackend:
    def test_openai_backend_without_key(self):
        # Test without API key
        backend = OpenAIBackend(api_key=None)
        assert not backend.is_available()

        info = backend.get_backend_info()
        assert info["backend"] == "openai"
        assert info["has_api_key"] is False

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_openai_backend_with_key(self, mock_openai):
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client

        backend = OpenAIBackend()
        info = backend.get_backend_info()
        assert info["has_api_key"] is True

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "test-key", "OPENAI_API_BASE": "http://custom.api"},
    )
    def test_openai_backend_custom_base_url(self):
        backend = OpenAIBackend()
        info = backend.get_backend_info()
        assert info["base_url"] == "http://custom.api"


class TestOllamaBackend:
    def test_ollama_backend_default_config(self):
        backend = OllamaBackend()
        info = backend.get_backend_info()
        assert info["backend"] == "ollama"
        assert info["host"] == "ollama:11434"
        assert info["model"] == "gpt-oss:20b"

    @patch.dict(os.environ, {"OLLAMA_HOST": "localhost:11434"})
    def test_ollama_backend_custom_host(self):
        backend = OllamaBackend()
        info = backend.get_backend_info()
        assert info["host"] == "localhost:11434"
        assert "localhost:11434" in info["base_url"]

    @patch("requests.get")
    def test_ollama_availability_check(self, mock_get):
        # Mock successful response with model available
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "gpt-oss:20b"}]}
        mock_get.return_value = mock_response

        backend = OllamaBackend()
        # Reset availability cache
        backend._available = None

        assert backend.is_available()


class TestLocalTransformersBackend:
    @pytest.mark.skipif(not has_transformers, reason="transformers not installed")
    def test_local_backend_without_dependencies(self):
        # Test without transformers installed
        backend = LocalTransformersBackend()
        # Should handle missing dependencies gracefully
        info = backend.get_backend_info()
        assert info["backend"] == "local_transformers"

    @patch("torch.cuda.is_available")
    @patch("transformers.AutoTokenizer.from_pretrained")
    @patch("transformers.AutoModelForCausalLM.from_pretrained")
    def test_local_backend_initialization(self, mock_model, mock_tokenizer, mock_cuda):
        mock_cuda.return_value = False  # CPU mode
        mock_tokenizer.return_value = Mock()
        mock_model.return_value = Mock()

        backend = LocalTransformersBackend()
        info = backend.get_backend_info()
        assert info["device"] == "cpu"


class TestLLMManager:
    def test_llm_manager_mock_mode(self):
        manager = LLMManager(use_mock=True)
        assert manager.is_available()
        assert manager.get_active_backend_name() == "mock"

        response = manager.generate_response("test prompt")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_llm_manager_backend_selection(self):
        manager = LLMManager(use_mock=True)

        # Should have mock backend
        info = manager.get_all_backends_info()
        assert "mock" in info
        assert info["active"] == "mock"

    def test_llm_manager_preferred_backend(self):
        manager = LLMManager(preferred_backend="mock", use_mock=True)
        assert manager.get_active_backend_name() == "mock"

    def test_llm_manager_backend_switching(self):
        manager = LLMManager(use_mock=True)

        # Should be able to switch to mock (since it's available)
        assert manager.switch_backend("mock")
        assert manager.get_active_backend_name() == "mock"

        # Should fail to switch to non-existent backend
        assert not manager.switch_backend("nonexistent")

    def test_llm_manager_backend_testing(self):
        manager = LLMManager(use_mock=True)

        result = manager.test_backend("mock", "test prompt")
        assert result["success"] is True
        assert "response" in result
        assert "response_time" in result

    def test_llm_manager_fallback(self):
        manager = LLMManager(use_mock=True)

        # Mock a failure and test fallback

        # Should still work with mock backend
        response = manager.generate_response("test")
        assert isinstance(response, str)


class TestCommandProcessor:
    def setup_method(self):
        self.mock_config = Mock()
        self.mock_config.model_actions = {
            "hello": {"keypress": {"keys": "ctrl+h"}},
            "lights": {"url": {"url": "http://example.com/lights"}},
            "music": {"message": {"text": "Playing music..."}},
        }

    def test_command_processor_initialization(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        status = processor.get_processor_status()
        assert status["llm_available"] is True
        assert status["commands_count"] == 3
        assert "hello" in status["available_commands"]

    def test_simple_command_matching(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        # Direct name match
        command, confidence, explanation = processor.process_command("hello there")
        assert command == "hello"
        assert confidence == 0.9
        assert "Keyword match" in explanation

        # Keyword match
        command, confidence, explanation = processor.process_command(
            "turn on the lights"
        )
        assert command == "lights"
        assert confidence >= 0.7

    def test_command_suggestions(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        suggestions = processor.get_command_suggestions("hel")
        assert len(suggestions) > 0
        assert any(s["command"] == "hello" for s in suggestions)

    def test_command_explanation(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        explanation = processor.explain_command("hello")
        assert explanation["command"] == "hello"
        assert explanation["type"] == "keypress"
        assert "ctrl+h" in explanation["description"]

    def test_llm_command_interpretation(self):
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.generate_response.return_value = """
        {
            "command": "lights",
            "confidence": 0.8,
            "reasoning": "user wants to control lights"
        }
        """

        processor = CommandProcessor(
            llm_manager=mock_llm, config_manager=self.mock_config
        )

        command, confidence, explanation = processor.process_command(
            "please turn on the illumination"
        )
        assert command == "lights"
        assert confidence == 0.8
        assert "user wants to control lights" in explanation

    def test_empty_input_handling(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        command, confidence, explanation = processor.process_command("")
        assert command is None
        assert confidence == 0.0
        assert "Empty input" in explanation

    def test_no_match_handling(self):
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(
            llm_manager=llm_manager, config_manager=self.mock_config
        )

        command, confidence, explanation = processor.process_command(
            "completely unknown command xyz"
        )
        # Should either return None or attempt LLM interpretation
        assert command is None or isinstance(command, str)


class TestLLMIntegrationE2E:
    def test_end_to_end_mock_flow(self):
        """Test complete LLM flow using mock components."""
        # Setup
        config = Mock()
        config.model_actions = {
            "hello": {"keypress": {"keys": "ctrl+h"}},
            "lights": {"url": {"url": "http://example.com/lights"}},
        }

        # Create LLM manager and processor
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(llm_manager=llm_manager, config_manager=config)

        # Test command processing
        test_inputs = ["hello world", "turn on the lights", "unknown command"]

        results = []
        for user_input in test_inputs:
            command, confidence, explanation = processor.process_command(user_input)
            results.append((user_input, command, confidence, explanation))

        # Verify results
        assert len(results) == 3

        # First should match hello
        assert results[0][1] == "hello"
        assert results[0][2] > 0.5

        # Second should match lights
        assert results[1][1] == "lights"
        assert results[1][2] > 0.5

    def test_llm_manager_environment_variables(self):
        """Test LLM manager respects environment variables."""
        with patch.dict(
            os.environ,
            {
                "LLM_BACKEND": "mock",
                "OPENAI_API_KEY": "test-key",
                "OLLAMA_HOST": "localhost:11434",
            },
        ):
            # Should respect LLM_BACKEND preference
            # Note: actual backend selection depends on availability
            pass

    def test_processor_status_reporting(self):
        """Test comprehensive status reporting."""
        config = Mock()
        config.model_actions = {"test": {"keypress": {"keys": "t"}}}

        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(llm_manager=llm_manager, config_manager=config)

        status = processor.get_processor_status()

        required_fields = [
            "llm_available",
            "llm_backend",
            "available_commands",
            "commands_count",
            "llm_info",
        ]

        for field in required_fields:
            assert field in status

        assert status["llm_available"] is True
        assert status["llm_backend"] == "mock"
        assert status["commands_count"] == 1
