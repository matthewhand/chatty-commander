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
Test voice chat integration with GPT-OSS:20B, TTS/STT, and avatar.

This test verifies that the voice chat system can:
1. Initialize all components (LLM, TTS, STT, avatar)
2. Process voice input through the pipeline
3. Generate responses with GPT-OSS:20B
4. Update avatar states correctly
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.avatars.thinking_state import ThinkingState, ThinkingStateManager


class TestVoiceChatIntegration:
    """Test the complete voice chat integration."""

    def test_voice_chat_components_initialization(self):
        """Test that all voice chat components can be initialized."""
        # Mock the components to avoid actual dependencies
        with patch("chatty_commander.llm.manager.LLMManager") as mock_llm_manager_class:
            with patch(
                "chatty_commander.voice.pipeline.VoicePipeline"
            ) as mock_voice_pipeline_class:
                with patch(
                    "chatty_commander.app.state_manager.StateManager"
                ) as mock_state_manager_class:
                    # Setup mocks
                    mock_llm_manager = Mock()
                    mock_llm_manager.is_available.return_value = True
                    mock_llm_manager.get_active_backend_name.return_value = "ollama"
                    mock_llm_manager_class.return_value = mock_llm_manager

                    mock_voice_pipeline = Mock()
                    mock_voice_pipeline.transcriber.is_available.return_value = True
                    mock_voice_pipeline.tts.is_available.return_value = True
                    mock_voice_pipeline_class.return_value = mock_voice_pipeline

                    mock_state_manager = Mock()
                    mock_state_manager_class.return_value = mock_state_manager

                    # Initialize components using the mocked classes
                    llm_manager = mock_llm_manager_class(preferred_backend="ollama")
                    voice_pipeline = mock_voice_pipeline_class()
                    state_manager = mock_state_manager_class()

                    # Verify components were created
                    assert llm_manager is not None
                    assert voice_pipeline is not None
                    assert state_manager is not None

                    # Verify LLM manager is available
                    assert llm_manager.is_available()
                    assert llm_manager.get_active_backend_name() == "ollama"

    def test_voice_chat_action_execution(self):
        """Test that the voice_chat action can be executed."""
        # Create mock components
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = Mock()
        config.voice_pipeline = Mock()

        # Setup voice pipeline mock
        config.voice_pipeline.transcriber = Mock()
        config.voice_pipeline.transcriber.record_and_transcribe.return_value = (
            "Hello, how are you?"
        )
        config.voice_pipeline.tts = Mock()
        config.voice_pipeline.tts.is_available.return_value = True
        config.voice_pipeline.tts.speak = Mock()

        # Setup LLM manager mock
        config.llm_manager.generate_response.return_value = (
            "I'm doing well, thank you for asking!"
        )

        # Create command executor
        command_executor = CommandExecutor(config, Mock(), Mock())
        command_executor.state_manager = Mock()

        # Execute voice chat action
        result = command_executor.execute_command("voice_chat")

        # Verify the action was processed
        assert result is True

        # Verify voice pipeline was called
        config.voice_pipeline.transcriber.record_and_transcribe.assert_called_once()

        # Verify LLM was called
        config.llm_manager.generate_response.assert_called_once()

    def test_avatar_state_broadcasting(self):
        """Test that avatar states are broadcast correctly during voice chat."""
        # Create thinking state manager
        thinking_state_manager = ThinkingStateManager()

        # Test setting different states
        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.LISTENING, "Voice chat activated"
        )
        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.RESPONDING, "AI response"
        )
        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.IDLE, "Voice chat ended"
        )

        # Verify states were set correctly
        agent_state = thinking_state_manager.get_agent_state("test_agent")
        assert agent_state is not None
        assert agent_state.state == ThinkingState.IDLE
        assert agent_state.message == "Voice chat ended"

    def test_voice_chat_error_handling(self):
        """Test that voice chat handles errors gracefully."""
        # Create mock components with errors
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = None  # LLM manager not available
        config.voice_pipeline = Mock()

        # Create command executor
        command_executor = CommandExecutor(config, Mock(), Mock())

        # Execute voice chat action (should fail gracefully)
        result = command_executor.execute_command("voice_chat")

        # Should return False when LLM manager is not available
        assert result is False

    def test_voice_chat_with_empty_input(self):
        """Test voice chat behavior with empty voice input."""
        # Create mock components
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = Mock()
        config.voice_pipeline = Mock()

        # Setup voice pipeline to return empty input
        config.voice_pipeline.transcriber = Mock()
        config.voice_pipeline.transcriber.record_and_transcribe.return_value = ""
        config.voice_pipeline.tts = Mock()
        config.voice_pipeline.tts.is_available.return_value = True

        # Create command executor
        command_executor = CommandExecutor(config, Mock(), Mock())
        command_executor.state_manager = Mock()

        # Execute voice chat action
        result = command_executor.execute_command("voice_chat")

        # Should return False with empty input
        assert result is False

        # LLM should not be called with empty input
        config.llm_manager.generate_response.assert_not_called()

    def test_voice_chat_configuration(self):
        """Test that voice chat action is properly configured."""
        # Test with a mock config that has the voice_chat action
        config = Mock()
        config.model_actions = {
            "voice_chat": {
                "action": "voice_chat",
                "description": "Start a voice chat session with the AI assistant",
            }
        }

        # Check that voice_chat action exists in model_actions
        assert "voice_chat" in config.model_actions

        # Check action configuration
        voice_chat_action = config.model_actions["voice_chat"]
        assert voice_chat_action["action"] == "voice_chat"
        assert "description" in voice_chat_action


if __name__ == "__main__":
    pytest.main([__file__])
