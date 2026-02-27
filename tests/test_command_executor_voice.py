
from unittest.mock import MagicMock, patch
import pytest
from chatty_commander.app.command_executor import CommandExecutor

class TestCommandExecutorVoice:
    """Tests for voice chat execution in CommandExecutor."""

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        config = MagicMock()
        model_manager = MagicMock()
        state_manager = MagicMock()
        return config, model_manager, state_manager

    def test_execute_voice_chat_success(self, mock_deps):
        """Test successful execution of voice chat."""
        config, model_manager, state_manager = mock_deps

        # Setup voice pipeline and llm manager mocks
        voice_pipeline = MagicMock()
        voice_pipeline.transcriber.record_and_transcribe.return_value = "hello"
        voice_pipeline.tts.is_available.return_value = True

        llm_manager = MagicMock()
        llm_manager.generate_response.return_value = "Hi there"

        config.voice_pipeline = voice_pipeline
        config.llm_manager = llm_manager

        executor = CommandExecutor(config, model_manager, state_manager)

        # We need to access the private method via a public interface or bypass protection for testing
        # Since _execute_voice_chat is called by execute_command when action="voice_chat",
        # we can test via execute_command if we mock the config properly.

        # But here we want to unit test the method logic specifically.
        # It's better to test through public API but for this specific "extra" task,
        # let's verify via direct call or by setting up the config for execute_command.

        # Let's use execute_command to be clean.
        config.model_actions = {"chat": {"action": "voice_chat"}}

        success = executor.execute_command("chat")

        assert success is True
        voice_pipeline.transcriber.record_and_transcribe.assert_called_once()
        llm_manager.generate_response.assert_called_once_with("hello")
        voice_pipeline.tts.speak.assert_called_once_with("Hi there")

    def test_execute_voice_chat_missing_components(self, mock_deps):
        """Test voice chat fails when components are missing."""
        config, model_manager, state_manager = mock_deps
        # Missing voice_pipeline
        config.voice_pipeline = None
        config.llm_manager = MagicMock()

        executor = CommandExecutor(config, model_manager, state_manager)
        config.model_actions = {"chat": {"action": "voice_chat"}}

        # We expect it to return False and log an error
        with patch("chatty_commander.app.command_executor.logging") as mock_logging:
            success = executor.execute_command("chat")
            assert success is False
            # Verify report_error was called (which logs critical)
            mock_logging.critical.assert_called()

    def test_execute_voice_chat_no_input(self, mock_deps):
        """Test voice chat handles no input gracefully."""
        config, model_manager, state_manager = mock_deps

        voice_pipeline = MagicMock()
        voice_pipeline.transcriber.record_and_transcribe.return_value = "" # No input

        llm_manager = MagicMock()

        config.voice_pipeline = voice_pipeline
        config.llm_manager = llm_manager

        executor = CommandExecutor(config, model_manager, state_manager)
        config.model_actions = {"chat": {"action": "voice_chat"}}

        success = executor.execute_command("chat")

        assert success is False
        voice_pipeline.transcriber.record_and_transcribe.assert_called_once()
        llm_manager.generate_response.assert_not_called()
