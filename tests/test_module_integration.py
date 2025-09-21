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
Tests for additional modules that exist in the codebase.
Tests AI, advisors, voice, and other core modules.
"""


import pytest

from chatty_commander.exceptions import ValidationError


class TestAIModuleComponents:
    """Test AI module components."""

    def test_intelligence_core_import(self):
        """Test intelligence core import."""
        try:
            from chatty_commander.ai.intelligence_core import IntelligenceCore

            core = IntelligenceCore({})
            assert core is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestAdvisorsModuleComponents:
    """Test advisors module components."""

    def test_conversation_engine_import(self):
        """Test conversation engine import."""
        try:
            from chatty_commander.advisors.conversation_engine import ConversationEngine

            engine = ConversationEngine({})
            assert engine is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestVoiceModuleComponents:
    """Test voice module components."""

    def test_enhanced_processor_import(self):
        """Test enhanced voice processor import."""
        try:
            from chatty_commander.voice.enhanced_processor import (
                EnhancedVoiceProcessor,
                VoiceProcessingConfig,
            )

            config = VoiceProcessingConfig()
            processor = EnhancedVoiceProcessor(config)
            assert processor is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestAppModuleComponents:
    """Test app module components."""

    def test_orchestrator_import(self):
        """Test orchestrator import."""
        try:
            from chatty_commander.app.orchestrator import (
                ComponentStatus,
                Orchestrator,
                OrchestratorConfig,
                OrchestratorState,
            )

            config = OrchestratorConfig()
            state = OrchestratorState.INITIALIZING
            status = ComponentStatus("test_component")
            orchestrator = Orchestrator(config)
            assert orchestrator is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestWebModuleComponents:
    """Test web module components."""

    def test_web_auth_import(self):
        """Test web auth import."""
        try:
            from unittest.mock import Mock

            from chatty_commander.web.middleware.auth import AuthMiddleware

            app = Mock()
            config_manager = Mock()
            middleware = AuthMiddleware(app, config_manager)
            assert middleware is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestLLMModuleComponents:
    """Test LLM module components."""

    def test_llm_manager_import(self):
        """Test LLM manager import."""
        try:
            from chatty_commander.llm.manager import LLMManager

            manager = LLMManager()
            assert manager is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestModelManagerComponents:
    """Test model manager components."""

    def test_model_manager_import(self):
        """Test model manager import."""
        try:
            from unittest.mock import Mock

            from chatty_commander.model_manager import ModelManager

            # Create a mock config object with required attributes
            config = Mock()
            config.general_models_path = "/tmp"
            config.system_models_path = "/tmp"
            config.chat_models_path = "/tmp"

            manager = ModelManager(config)
            assert manager is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestProvidersComponents:
    """Test providers components."""

    def test_ollama_provider_import(self):
        """Test Ollama provider import."""
        try:
            from chatty_commander.providers.ollama_provider import OllamaProvider

            provider = OllamaProvider({})
            assert provider is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestToolsComponents:
    """Test tools components."""

    def test_bridge_nodejs_import(self):
        """Test NodeJS bridge import."""
        try:
            from chatty_commander.tools.bridge_nodejs import generate_package_json

            result = generate_package_json()
            assert isinstance(result, str)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestUtilsComponents:
    """Test utils components."""

    def test_logger_import(self):
        """Test logger import."""
        try:
            from chatty_commander.utils.logger import setup_logger

            logger = setup_logger("test")
            assert logger is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestIntegrationTests:
    """Test integration between modules."""

    def test_cross_module_imports(self):
        """Test that modules can import each other."""
        try:
            from chatty_commander.advisors.conversation_engine import ConversationEngine
            from chatty_commander.ai.intelligence_core import IntelligenceCore
            from chatty_commander.voice.enhanced_processor import EnhancedVoiceProcessor

            # Test that they can be instantiated together
            engine = ConversationEngine({})
            core = IntelligenceCore({})
            assert engine is not None
            assert core is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestExceptionIntegration:
    """Test exception handling across modules."""

    def test_validation_error_usage(self):
        """Test ValidationError usage in different contexts."""
        try:
            from chatty_commander.app.orchestrator import OrchestratorConfig

            # Test that ValidationError is raised appropriately
            try:
                OrchestratorConfig(max_concurrent_operations=-1)
                assert False, "Should have raised ValidationError"
            except ValidationError:
                assert True  # Expected
            except Exception as e:
                pytest.fail(f"Unexpected exception: {e}")
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
