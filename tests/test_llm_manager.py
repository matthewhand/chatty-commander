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
Comprehensive tests for LLM manager module.

Tests automatic backend selection and fallback functionality.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.llm.manager import LLMManager


class TestLLMManager:
    """Comprehensive tests for LLMManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            "providers": ["openai", "ollama", "local"],
            "default_provider": "openai",
            "openai_api_key": "test-key",
            "ollama_base_url": "http://localhost:11434",
            "max_retries": 3,
            "timeout": 30,
        }

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "config"}')
            config_path = f.name

        try:
            yield config_path
        finally:
            os.unlink(config_path)

    def test_llm_manager_initialization(self, mock_config):
        """Test LLMManager initialization."""
        manager = LLMManager(mock_config)

        assert manager.config == mock_config
        assert manager.current_backend is None
        assert manager.fallback_chain == ["openai", "ollama", "local", "mock"]

    def test_backend_selection_openai_available(self, mock_config):
        """Test backend selection when OpenAI is available."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._is_openai_available"
        ) as mock_available:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._is_ollama_available"
            ) as mock_ollama:
                with patch(
                    "src.chatty_commander.llm.manager.LLMManager._is_local_available"
                ) as mock_local:
                    mock_available.return_value = True
                    mock_ollama.return_value = False
                    mock_local.return_value = False

                    manager = LLMManager(mock_config)
                    backend = manager._select_backend()

                    assert backend == "openai"
                    mock_available.assert_called_once()

    def test_backend_selection_ollama_fallback(self, mock_config):
        """Test backend selection with OpenAI unavailable, Ollama available."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._is_openai_available"
        ) as mock_openai:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._is_ollama_available"
            ) as mock_ollama:
                with patch(
                    "src.chatty_commander.llm.manager.LLMManager._is_local_available"
                ) as mock_local:
                    mock_openai.return_value = False
                    mock_ollama.return_value = True
                    mock_local.return_value = False

                    manager = LLMManager(mock_config)
                    backend = manager._select_backend()

                    assert backend == "ollama"

    def test_backend_selection_local_fallback(self, mock_config):
        """Test backend selection with OpenAI and Ollama unavailable, local available."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._is_openai_available"
        ) as mock_openai:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._is_ollama_available"
            ) as mock_ollama:
                with patch(
                    "src.chatty_commander.llm.manager.LLMManager._is_local_available"
                ) as mock_local:
                    mock_openai.return_value = False
                    mock_ollama.return_value = False
                    mock_local.return_value = True

                    manager = LLMManager(mock_config)
                    backend = manager._select_backend()

                    assert backend == "local"

    def test_backend_selection_mock_fallback(self, mock_config):
        """Test backend selection when all backends unavailable except mock."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._is_openai_available"
        ) as mock_openai:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._is_ollama_available"
            ) as mock_ollama:
                with patch(
                    "src.chatty_commander.llm.manager.LLMManager._is_local_available"
                ) as mock_local:
                    mock_openai.return_value = False
                    mock_ollama.return_value = False
                    mock_local.return_value = False

                    manager = LLMManager(mock_config)
                    backend = manager._select_backend()

                    assert backend == "mock"

    def test_openai_availability_check_with_api_key(self, mock_config):
        """Test OpenAI availability check with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            manager = LLMManager(mock_config)
            available = manager._is_openai_available()

            assert available is True

    def test_openai_availability_check_without_api_key(self, mock_config):
        """Test OpenAI availability check without API key."""
        with patch.dict(os.environ, {}, clear=True):
            manager = LLMManager(mock_config)
            available = manager._is_openai_available()

            assert available is False

    def test_ollama_availability_check_server_up(self, mock_config):
        """Test Ollama availability check when server is up."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200

            manager = LLMManager(mock_config)
            available = manager._is_ollama_available()

            assert available is True
            mock_get.assert_called_once()

    def test_ollama_availability_check_server_down(self, mock_config):
        """Test Ollama availability check when server is down."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            manager = LLMManager(mock_config)
            available = manager._is_ollama_available()

            assert available is False

    def test_local_transformers_availability_check(self, mock_config):
        """Test local transformers availability check."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._has_transformers"
        ) as mock_has:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._has_torch"
            ) as mock_torch:
                mock_has.return_value = True
                mock_torch.return_value = True

                manager = LLMManager(mock_config)
                available = manager._is_local_available()

                assert available is True

    def test_transformers_availability_check_missing_deps(self, mock_config):
        """Test transformers availability check with missing dependencies."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._has_transformers"
        ) as mock_has:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._has_torch"
            ) as mock_torch:
                mock_has.return_value = False
                mock_torch.return_value = True

                manager = LLMManager(mock_config)
                available = manager._is_local_available()

                assert available is False

    def test_backend_initialization_openai(self, mock_config):
        """Test OpenAI backend initialization."""
        with patch(
            "src.chatty_commander.llm.manager.OpenAIBackend"
        ) as mock_backend_class:
            mock_backend = Mock()
            mock_backend_class.return_value = mock_backend

            manager = LLMManager(mock_config)
            backend = manager._initialize_backend("openai")

            assert backend == mock_backend
            mock_backend_class.assert_called_once()

    def test_backend_initialization_ollama(self, mock_config):
        """Test Ollama backend initialization."""
        with patch(
            "src.chatty_commander.llm.manager.OllamaBackend"
        ) as mock_backend_class:
            mock_backend = Mock()
            mock_backend_class.return_value = mock_backend

            manager = LLMManager(mock_config)
            backend = manager._initialize_backend("ollama")

            assert backend == mock_backend
            mock_backend_class.assert_called_once_with("http://localhost:11434")

    def test_backend_initialization_local(self, mock_config):
        """Test local transformers backend initialization."""
        with patch(
            "src.chatty_commander.llm.manager.LocalTransformersBackend"
        ) as mock_backend_class:
            mock_backend = Mock()
            mock_backend_class.return_value = mock_backend

            manager = LLMManager(mock_config)
            backend = manager._initialize_backend("local")

            assert backend == mock_backend
            mock_backend_class.assert_called_once()

    def test_backend_initialization_mock(self, mock_config):
        """Test mock backend initialization."""
        with patch(
            "src.chatty_commander.llm.manager.MockLLMBackend"
        ) as mock_backend_class:
            mock_backend = Mock()
            mock_backend_class.return_value = mock_backend

            manager = LLMManager(mock_config)
            backend = manager._initialize_backend("mock")

            assert backend == mock_backend
            mock_backend_class.assert_called_once()

    def test_generate_with_successful_backend(self, mock_config):
        """Test generate method with successful backend."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._select_backend"
        ) as mock_select:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
            ) as mock_init:
                mock_backend = Mock()
                mock_backend.generate.return_value = "Generated response"
                mock_init.return_value = mock_backend
                mock_select.return_value = "openai"

                manager = LLMManager(mock_config)
                result = manager.generate("Test prompt")

                assert result == "Generated response"
                mock_backend.generate.assert_called_once_with("Test prompt")

    def test_generate_with_failing_backend_retry(self, mock_config):
        """Test generate method with failing backend and retry."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._select_backend"
        ) as mock_select:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
            ) as mock_init:
                mock_backend = Mock()
                mock_backend.generate.side_effect = [
                    Exception("First failure"),
                    "Success",
                ]
                mock_init.return_value = mock_backend
                mock_select.return_value = "openai"

                manager = LLMManager(mock_config)
                result = manager.generate("Test prompt")

                assert result == "Success"
                assert mock_backend.generate.call_count == 2

    def test_generate_with_all_backends_failing(self, mock_config):
        """Test generate method when all backends fail."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._select_backend"
        ) as mock_select:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
            ) as mock_init:
                mock_backend = Mock()
                mock_backend.generate.side_effect = Exception("All backends failed")
                mock_init.return_value = mock_backend
                mock_select.return_value = "mock"  # Last fallback

                manager = LLMManager(mock_config)
                result = manager.generate("Test prompt")

                # Should eventually succeed with mock backend
                assert result is not None

    def test_get_available_backends(self, mock_config):
        """Test getting available backends."""
        with patch(
            "src.chatty_commander.llm.manager.LLMManager._is_openai_available"
        ) as mock_openai:
            with patch(
                "src.chatty_commander.llm.manager.LLMManager._is_ollama_available"
            ) as mock_ollama:
                with patch(
                    "src.chatty_commander.llm.manager.LLMManager._is_local_available"
                ) as mock_local:
                    mock_openai.return_value = True
                    mock_ollama.return_value = True
                    mock_local.return_value = False

                    manager = LLMManager(mock_config)
                    available = manager.get_available_backends()

                    assert "openai" in available
                    assert "ollama" in available
                    assert "local" not in available
                    assert "mock" in available  # Mock is always available

    def test_switch_backend_manually(self, mock_config):
        """Test manual backend switching."""
        manager = LLMManager(mock_config)

        with patch(
            "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
        ) as mock_init:
            mock_backend = Mock()
            mock_init.return_value = mock_backend

            result = manager.switch_backend("ollama")

            assert result is True
            assert manager.current_backend == "ollama"
            assert manager.current_backend_instance == mock_backend

    def test_switch_to_invalid_backend(self, mock_config):
        """Test switching to invalid backend."""
        manager = LLMManager(mock_config)

        result = manager.switch_backend("invalid_backend")

        assert result is False
        assert manager.current_backend is None

    def test_backend_health_check(self, mock_config):
        """Test backend health checking."""
        manager = LLMManager(mock_config)

        with patch(
            "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
        ) as mock_init:
            mock_backend = Mock()
            mock_backend.health_check.return_value = True
            mock_init.return_value = mock_backend

            manager.switch_backend("openai")
            health = manager.health_check()

            assert health is True
            mock_backend.health_check.assert_called_once()

    def test_backend_health_check_failure(self, mock_config):
        """Test backend health check failure."""
        manager = LLMManager(mock_config)

        with patch(
            "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
        ) as mock_init:
            mock_backend = Mock()
            mock_backend.health_check.side_effect = Exception("Health check failed")
            mock_init.return_value = mock_backend

            manager.switch_backend("openai")
            health = manager.health_check()

            assert health is False

    def test_configuration_update(self, mock_config):
        """Test configuration update."""
        manager = LLMManager(mock_config)

        new_config = {
            "providers": ["ollama", "local"],
            "default_provider": "ollama",
            "max_retries": 5,
        }

        manager.update_config(new_config)

        assert manager.config["providers"] == ["ollama", "local"]
        assert manager.config["default_provider"] == "ollama"
        assert manager.config["max_retries"] == 5

    def test_get_current_backend_info(self, mock_config):
        """Test getting current backend information."""
        manager = LLMManager(mock_config)

        with patch(
            "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
        ) as mock_init:
            mock_backend = Mock()
            mock_backend.get_info.return_value = {"name": "OpenAI", "model": "gpt-4"}
            mock_init.return_value = mock_backend

            manager.switch_backend("openai")
            info = manager.get_current_backend_info()

            assert info == {"name": "OpenAI", "model": "gpt-4"}
            mock_backend.get_info.assert_called_once()

    def test_fallback_chain_customization(self, mock_config):
        """Test fallback chain customization."""
        custom_config = mock_config.copy()
        custom_config["fallback_chain"] = ["ollama", "local", "mock"]

        manager = LLMManager(custom_config)

        assert manager.fallback_chain == ["ollama", "local", "mock"]

    def test_error_handling_backend_initialization_failure(self, mock_config):
        """Test error handling when backend initialization fails."""
        manager = LLMManager(mock_config)

        with patch(
            "src.chatty_commander.llm.manager.LLMManager._initialize_backend"
        ) as mock_init:
            mock_init.side_effect = Exception("Initialization failed")

            result = manager.switch_backend("openai")

            assert result is False
            assert manager.current_backend is None

    def test_generate_with_empty_prompt(self, mock_config):
        """Test generate method with empty prompt."""
        manager = LLMManager(mock_config)

        result = manager.generate("")

        # Should handle empty prompt gracefully
        assert result is not None

    def test_generate_with_none_prompt(self, mock_config):
        """Test generate method with None prompt."""
        manager = LLMManager(mock_config)

        result = manager.generate(None)

        # Should handle None prompt gracefully
        assert result is not None
