# helpers/mocks.py
"""Shared mock factories for consistent test doubles."""

from unittest.mock import MagicMock, Mock


class MockFactory:
    """
    Factory for creating pre-configured mocks for common dependencies.
    
    This centralizes mock setup to ensure consistency across tests
    and reduce duplication.
    """
    
    @staticmethod
    def create_mock_config_manager(data=None):
        """Create a mock ConfigManager with sensible defaults."""
        config = Mock()
        config.wake_words = data.get("wake_words", ["hey test"]) if data else ["hey test"]
        config.default_state = data.get("default_state", "idle") if data else "idle"
        config.model_actions = data.get("model_actions", {}) if data else {}
        config.save_config = Mock(return_value=True)
        config.reload_config = Mock(return_value=True)
        config.validate = Mock(return_value=True)
        return config
    
    @staticmethod
    def create_mock_state_manager(state="idle"):
        """Create a mock StateManager."""
        sm = Mock()
        sm.current_state = state
        sm.change_state = Mock(return_value=True)
        sm.process_command = Mock(return_value=True)
        sm.get_active_models = Mock(return_value=["model1", "model2"])
        sm.add_state_change_callback = Mock()
        return sm
    
    @staticmethod
    def create_mock_model_manager(models=None):
        """Create a mock ModelManager."""
        mm = Mock()
        mm.get_models = Mock(return_value=models or ["model1", "model2", "model3"])
        mm.reload_models = Mock(return_value=True)
        mm.load_model = Mock(return_value=True)
        mm.unload_model = Mock(return_value=True)
        return mm
    
    @staticmethod
    def create_mock_command_executor():
        """Create a mock CommandExecutor."""
        ce = Mock()
        ce.validate_command = Mock(return_value=True)
        ce.execute_command = Mock(return_value=True)
        ce.get_command_history = Mock(return_value=[])
        return ce
    
    @staticmethod
    def create_mock_llm_manager(response="test response", available=True):
        """Create a mock LLMManager."""
        manager = Mock()
        manager.generate = Mock(return_value=response)
        manager.is_available = Mock(return_value=available)
        manager.get_backend_info = Mock(return_value={"backend": "mock"})
        return manager
    
    @staticmethod
    def create_mock_voice_pipeline(transcription="test transcription"):
        """Create a mock VoicePipeline."""
        pipeline = Mock()
        pipeline.process_audio = Mock(return_value=transcription)
        pipeline.start_listening = Mock()
        pipeline.stop_listening = Mock()
        pipeline.is_listening = False
        return pipeline
    
    @staticmethod
    def create_mock_wake_word_detector(detected_word=None):
        """Create a mock WakeWordDetector."""
        detector = Mock()
        detector.detected_word = detected_word
        detector.start = Mock()
        detector.stop = Mock()
        detector.is_running = False
        return detector
    
    @staticmethod
    def create_mock_transcriber(text="transcribed text"):
        """Create a mock VoiceTranscriber."""
        transcriber = Mock()
        transcriber.transcribe = Mock(return_value=text)
        transcriber.is_available = Mock(return_value=True)
        return transcriber
    
    @staticmethod
    def create_mock_web_server():
        """Create a mock web server components."""
        app = Mock()
        app.get = Mock()
        app.post = Mock()
        app.put = Mock()
        app.delete = Mock()
        
        client = Mock()
        client.get = Mock(return_value=Mock(status_code=200, json=Mock(return_value={})))
        client.post = Mock(return_value=Mock(status_code=201, json=Mock(return_value={})))
        
        return {"app": app, "client": client}
    
    @staticmethod
    def create_mock_avatar_manager():
        """Create a mock AvatarManager."""
        manager = Mock()
        manager.get_available_avatars = Mock(return_value=["default", "robot", "human"])
        manager.set_avatar = Mock(return_value=True)
        manager.get_current_avatar = Mock(return_value="default")
        return manager
    
    @staticmethod
    def create_full_mock_stack():
        """
        Create a complete mock stack of all major dependencies.
        
        Returns dict with all mocks pre-wired for integration testing.
        """
        return {
            "config": MockFactory.create_mock_config_manager(),
            "state_manager": MockFactory.create_mock_state_manager(),
            "model_manager": MockFactory.create_mock_model_manager(),
            "command_executor": MockFactory.create_mock_command_executor(),
            "llm_manager": MockFactory.create_mock_llm_manager(),
            "voice_pipeline": MockFactory.create_mock_voice_pipeline(),
            "wake_detector": MockFactory.create_mock_wake_word_detector(),
            "transcriber": MockFactory.create_mock_transcriber(),
        }


# Quick access functions for common patterns

def mock_config(**kwargs):
    """Quick function to create mock config."""
    return MockFactory.create_mock_config_manager(kwargs)


def mock_llm(response="test", available=True):
    """Quick function to create mock LLM."""
    return MockFactory.create_mock_llm_manager(response, available)


def mock_voice(text="test"):
    """Quick function to create mock voice pipeline."""
    return MockFactory.create_mock_voice_pipeline(text)


def mock_full_stack():
    """Quick function to create full mock stack."""
    return MockFactory.create_full_mock_stack()
