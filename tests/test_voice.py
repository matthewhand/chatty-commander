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

"""Consolidated voice tests: pipeline, transcription, wakeword, routes, chat integration."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.avatars.thinking_state import ThinkingState, ThinkingStateManager
from chatty_commander.voice import VoicePipeline, VoiceTranscriber
from chatty_commander.voice.transcription import MockTranscriptionBackend
from chatty_commander.voice.wakeword import MockWakeWordDetector
from chatty_commander.web.web_mode import create_app

# ── Mock wake-word detector ──────────────────────────────────────────────


class TestMockWakeWordDetector:
    def test_mock_detector_initialization(self):
        detector = MockWakeWordDetector()
        assert not detector.is_listening()
        assert detector.get_available_models() == ["hey_jarvis", "alexa", "hey_google"]

    def test_mock_detector_callbacks(self):
        detector = MockWakeWordDetector()
        callback_called = []

        def test_callback(wake_word, confidence):
            callback_called.append((wake_word, confidence))

        detector.add_callback(test_callback)
        detector.start_listening()
        detector.trigger_wake_word("hey_jarvis", 0.9)

        assert len(callback_called) == 1
        assert callback_called[0] == ("hey_jarvis", 0.9)

    def test_mock_detector_start_stop(self):
        detector = MockWakeWordDetector()
        assert not detector.is_listening()

        detector.start_listening()
        assert detector.is_listening()

        detector.stop_listening()
        assert not detector.is_listening()


# ── Mock transcription backend ───────────────────────────────────────────


class TestMockTranscriptionBackend:
    def test_mock_backend_transcription(self):
        backend = MockTranscriptionBackend()
        assert backend.is_available()

        result1 = backend.transcribe(b"dummy_audio")
        result2 = backend.transcribe(b"dummy_audio")

        assert result1 == "hello world"
        assert result2 == "turn on the lights"

    def test_mock_backend_custom_responses(self):
        responses = ["test response 1", "test response 2"]
        backend = MockTranscriptionBackend(responses=responses)

        result1 = backend.transcribe(b"dummy_audio")
        result2 = backend.transcribe(b"dummy_audio")
        result3 = backend.transcribe(b"dummy_audio")  # Should cycle back

        assert result1 == "test response 1"
        assert result2 == "test response 2"
        assert result3 == "test response 1"


# ── Voice transcriber ────────────────────────────────────────────────────


class TestVoiceTranscriber:
    def test_transcriber_with_mock_backend(self):
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.is_available()

        result = transcriber.transcribe_audio_data(b"dummy_audio")
        assert result == "hello world"

    def test_transcriber_backend_info(self):
        transcriber = VoiceTranscriber(backend="mock")
        info = transcriber.get_backend_info()

        assert "backend_type" in info
        assert "is_available" in info
        assert info["is_available"] is True
        assert info["sample_rate"] == 16000


# ── Voice pipeline ───────────────────────────────────────────────────────


class TestVoicePipeline:
    def setup_method(self):
        self.mock_config = Mock()
        self.mock_config.model_actions = {
            "hello": {"keypress": {"keys": "ctrl+h"}},
            "lights": {"url": {"url": "http://example.com/lights"}},
        }

        self.mock_executor = Mock()
        self.mock_executor.execute_command.return_value = True

        self.mock_state = Mock()

    def test_pipeline_initialization(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=self.mock_state,
            use_mock=True,
        )

        assert not pipeline.is_listening()
        status = pipeline.get_status()
        assert "listening" in status
        assert "transcriber_available" in status

    def test_pipeline_start_stop(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )

        pipeline.start()
        assert pipeline.is_listening()

        pipeline.stop()
        assert not pipeline.is_listening()

    def test_command_matching(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )

        command = pipeline._match_command("hello there")
        assert command == "hello"

        command = pipeline._match_command("turn on the lights please")
        assert command == "lights"

        command = pipeline._match_command("unknown command")
        assert command is None

    def test_text_command_processing(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )

        result = pipeline.process_text_command("hello world")
        assert result == "hello"
        self.mock_executor.execute_command.assert_called_with("hello")

    def test_command_callbacks(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )

        callback_calls = []

        def test_callback(command_name, transcription):
            callback_calls.append((command_name, transcription))

        pipeline.add_command_callback(test_callback)
        pipeline.process_text_command("hello there")

        assert len(callback_calls) == 1
        assert callback_calls[0] == ("hello", "hello there")

    def test_mock_wake_word_trigger(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )

        pipeline.trigger_mock_wake_word("hey_jarvis")

    def test_voice_only_invokes_tts(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
            tts_backend="mock",
            voice_only=True,
        )

        pipeline.process_text_command("hello there")
        assert pipeline.tts.backend.spoken[0] == "hello"

    def test_pipeline_without_managers(self):
        pipeline = VoicePipeline(use_mock=True)

        pipeline.start()
        assert pipeline.is_listening()

        result = pipeline.process_text_command("hello")
        assert result is None

        pipeline.stop()


# ── End-to-end mock flow ─────────────────────────────────────────────────


class TestVoiceIntegrationE2E:
    def test_end_to_end_mock_flow(self):
        """Test complete voice flow using mock components."""
        config = Mock()
        config.model_actions = {"hello": {"keypress": {"keys": "ctrl+h"}}}

        executor = Mock()
        executor.execute_command.return_value = True

        state_manager = Mock()

        pipeline = VoicePipeline(
            config_manager=config,
            command_executor=executor,
            state_manager=state_manager,
            use_mock=True,
        )

        commands_processed = []

        def command_callback(command_name, transcription):
            commands_processed.append((command_name, transcription))

        pipeline.add_command_callback(command_callback)

        pipeline.start()
        assert pipeline.is_listening()

        result = pipeline.process_text_command("hello world")
        assert result == "hello"

        executor.execute_command.assert_called_with("hello")
        assert len(commands_processed) == 1
        assert commands_processed[0] == ("hello", "hello world")

        pipeline.stop()
        assert not pipeline.is_listening()

    def test_voice_pipeline_status_reporting(self):
        """Test status reporting functionality."""
        pipeline = VoicePipeline(use_mock=True)

        status = pipeline.get_status()

        required_fields = [
            "listening",
            "processing",
            "wake_detector_available",
            "transcriber_available",
            "transcriber_info",
            "available_wake_words",
        ]

        for field in required_fields:
            assert field in status

        assert isinstance(status["transcriber_info"], dict)
        assert isinstance(status["available_wake_words"], list)


# ── Voice chat integration (mock-based) ──────────────────────────────────


class TestVoiceChatIntegration:
    """Test the complete voice chat integration."""

    def test_voice_chat_components_initialization(self):
        """Test that all voice chat components can be initialized."""
        with patch("chatty_commander.llm.manager.LLMManager") as mock_llm_manager_class:
            with patch(
                "chatty_commander.voice.pipeline.VoicePipeline"
            ) as mock_voice_pipeline_class:
                with patch(
                    "chatty_commander.app.state_manager.StateManager"
                ) as mock_state_manager_class:
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

                    llm_manager = mock_llm_manager_class(preferred_backend="ollama")
                    voice_pipeline = mock_voice_pipeline_class()
                    state_manager = mock_state_manager_class()

                    assert llm_manager is not None
                    assert voice_pipeline is not None
                    assert state_manager is not None

                    assert llm_manager.is_available()
                    assert llm_manager.get_active_backend_name() == "ollama"

    def test_voice_chat_action_execution(self):
        """Test that the voice_chat action can be executed."""
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = Mock()
        config.voice_pipeline = Mock()

        config.voice_pipeline.transcriber = Mock()
        config.voice_pipeline.transcriber.record_and_transcribe.return_value = (
            "Hello, how are you?"
        )
        config.voice_pipeline.tts = Mock()
        config.voice_pipeline.tts.is_available.return_value = True
        config.voice_pipeline.tts.speak = Mock()

        config.llm_manager.generate_response.return_value = (
            "I'm doing well, thank you for asking!"
        )

        command_executor = CommandExecutor(config, Mock(), Mock())
        command_executor.state_manager = Mock()

        result = command_executor.execute_command("voice_chat")
        assert result is True

        config.voice_pipeline.transcriber.record_and_transcribe.assert_called_once()
        config.llm_manager.generate_response.assert_called_once()

    def test_avatar_state_broadcasting(self):
        """Test that avatar states are broadcast correctly during voice chat."""
        thinking_state_manager = ThinkingStateManager()

        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.LISTENING, "Voice chat activated"
        )
        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.RESPONDING, "AI response"
        )
        thinking_state_manager.set_agent_state(
            "test_agent", ThinkingState.IDLE, "Voice chat ended"
        )

        agent_state = thinking_state_manager.get_agent_state("test_agent")
        assert agent_state is not None
        assert agent_state.state == ThinkingState.IDLE
        assert agent_state.message == "Voice chat ended"

    def test_voice_chat_error_handling(self):
        """Test that voice chat handles errors gracefully."""
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = None
        config.voice_pipeline = Mock()

        command_executor = CommandExecutor(config, Mock(), Mock())

        result = command_executor.execute_command("voice_chat")
        assert result is False

    def test_voice_chat_with_empty_input(self):
        """Test voice chat behavior with empty voice input."""
        config = Mock()
        config.model_actions = {"voice_chat": {"action": "voice_chat"}}
        config.llm_manager = Mock()
        config.voice_pipeline = Mock()

        config.voice_pipeline.transcriber = Mock()
        config.voice_pipeline.transcriber.record_and_transcribe.return_value = ""
        config.voice_pipeline.tts = Mock()
        config.voice_pipeline.tts.is_available.return_value = True

        command_executor = CommandExecutor(config, Mock(), Mock())
        command_executor.state_manager = Mock()

        result = command_executor.execute_command("voice_chat")
        assert result is False

        config.llm_manager.generate_response.assert_not_called()

    def test_voice_chat_configuration(self):
        """Test that voice chat action is properly configured."""
        config = Mock()
        config.model_actions = {
            "voice_chat": {
                "action": "voice_chat",
                "description": "Start a voice chat session with the AI assistant",
            }
        }

        assert "voice_chat" in config.model_actions

        voice_chat_action = config.model_actions["voice_chat"]
        assert voice_chat_action["action"] == "voice_chat"
        assert "description" in voice_chat_action


# ── Voice routes (TestClient) ────────────────────────────────────────────


class TestVoiceRoutes:
    @pytest.fixture
    def config(self):
        cfg = Config(config_file="")
        cfg.config = {
            "wake_words": ["hey computer", "jarvis"],
            "voice": {"backend": "test_backend"},
        }
        return cfg

    @pytest.fixture
    def client(self, config):
        state_mgr = StateManager(config)
        model_mgr = ModelManager(config)
        executor = CommandExecutor(config, model_mgr, state_mgr)
        app = create_app(
            config_manager=config,
            state_manager=state_mgr,
            model_manager=model_mgr,
            command_executor=executor,
            no_auth=True,
        )
        return TestClient(app)

    def test_voice_status(self, client):
        response = client.get("/api/voice/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert data["running"] is False
        assert data["wake_words"] == ["hey computer", "jarvis"]
        assert data["backend"] == "test_backend"

    def test_voice_start_and_stop(self, client):
        status_resp = client.get("/api/voice/status")
        assert status_resp.json()["running"] is False

        start_resp = client.post("/api/voice/start")
        assert start_resp.status_code == 200
        assert start_resp.json()["status"] == "started"

        status_resp = client.get("/api/voice/status")
        assert status_resp.json()["running"] is True

        start_resp_again = client.post("/api/voice/start")
        assert start_resp_again.status_code == 200
        assert start_resp_again.json()["status"] == "already_running"

        stop_resp = client.post("/api/voice/stop")
        assert stop_resp.status_code == 200
        assert stop_resp.json()["status"] == "stopped"

        status_resp = client.get("/api/voice/status")
        assert status_resp.json()["running"] is False

        stop_resp_again = client.post("/api/voice/stop")
        assert stop_resp_again.status_code == 200
        assert stop_resp_again.json()["status"] == "already_stopped"


# ── Voice recognition integration (state transitions) ────────────────────


class TestVoiceRecognitionIntegration:
    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    @pytest.fixture
    def model_manager(self, config):
        return ModelManager(config)

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["dummy.onnx"])
    def test_voice_recognition_integration_idle(
        self, mock_listdir, mock_exists, state_manager, model_manager
    ):
        """Test integration in idle state."""
        state_manager.change_state("idle")
        model_manager.reload_models("idle")
        assert len(model_manager.active_models) > 0
        with (
            patch(
                "chatty_commander.app.model_manager.random.random", return_value=0.01
            ),
            patch(
                "chatty_commander.app.model_manager.random.choice",
                return_value="hey_chat_tee",
            ),
            patch("time.sleep"),
        ):
            detected = model_manager.listen_for_commands()
            assert detected == "hey_chat_tee"
            new_state = state_manager.update_state(detected)
            assert new_state == "chatty"

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["dummy.onnx"])
    def test_voice_recognition_integration_chatty(
        self, mock_listdir, mock_exists, state_manager, model_manager
    ):
        """Test integration in chatty state."""
        state_manager.change_state("chatty")
        model_manager.reload_models("chatty")
        assert len(model_manager.active_models) > 0
        with (
            patch(
                "chatty_commander.app.model_manager.random.random", return_value=0.01
            ),
            patch(
                "chatty_commander.app.model_manager.random.choice",
                return_value="okay_stop",
            ),
            patch("time.sleep"),
        ):
            detected = model_manager.listen_for_commands()
            assert detected == "okay_stop"
            new_state = state_manager.update_state(detected)
            assert new_state == "idle"

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["dummy.onnx"])
    def test_no_detection_integration(
        self, mock_listdir, mock_exists, state_manager, model_manager
    ):
        """Test no detection case."""
        state_manager.change_state("computer")
        model_manager.reload_models("computer")
        with (
            patch("chatty_commander.app.model_manager.random.random", return_value=0.1),
            patch("time.sleep"),
        ):
            detected = model_manager.listen_for_commands()
            assert detected is None
            new_state = state_manager.update_state("invalid")
            assert new_state is None
            assert state_manager.current_state == "computer"
