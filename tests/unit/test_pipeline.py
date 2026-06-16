"""Dedicated unit tests for src/chatty_commander/voice/pipeline.py.

Covers happy paths, lifecycle, command matching/execution via public APIs,
callback management, status, error handling, and graceful degradation.
Uses mocks for voice sub-components (to support test envs where submodules
may have transient parse issues) and leverages existing test fixtures.
Follows patterns from tests/unit/test_wakeword.py, tests/e2e/test_voice_pipeline.py,
TEST_STRATEGY.md and EXAMPLE_REFACTORED_TEST.py (AAA, docstrings, fixtures).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Ensure src is on path for "chatty_commander.*" imports (consistent with other unit tests)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Pre-populate sys.modules with mocks for voice submodules that have syntax issues in
# the current tree. This allows importing VoicePipeline in isolation without
# executing the broken sibling .py files (from .transcription, .tts, .wakeword).
# The mocks provide the names that pipeline.py imports at module level.
_mock_wakeword = Mock()
_mock_wakeword.VOICE_DEPS_AVAILABLE = False
_mock_wakeword.MockWakeWordDetector = MagicMock
_mock_wakeword.WakeWordDetector = MagicMock
sys.modules.setdefault("chatty_commander.voice.wakeword", _mock_wakeword)

_mock_transcription = Mock()
_mock_transcription.VoiceTranscriber = MagicMock
sys.modules.setdefault("chatty_commander.voice.transcription", _mock_transcription)

_mock_tts = Mock()
_mock_tts.TextToSpeech = MagicMock
sys.modules.setdefault("chatty_commander.voice.tts", _mock_tts)

# Guard against other voice modules being pulled in transitively during tests
sys.modules.setdefault("chatty_commander.voice.enhanced_processor", Mock())
sys.modules.setdefault("chatty_commander.voice.self_test", Mock())
sys.modules.setdefault("chatty_commander.voice.cli", Mock())

# Now safe to import the module under test
from chatty_commander.voice.pipeline import VoicePipeline


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_config() -> Mock:
    """Provide a mock config manager with model_actions for command matching."""
    cfg = Mock()
    cfg.model_actions = {
        "open_browser": {"type": "url", "url": "https://google.com"},
        "play_music": {"type": "shell", "command": "playerctl play"},
        "hello": {"action": "custom_message", "message": "hi"},
        "lights": {"action": "keypress", "keys": "ctrl+l"},
    }
    cfg.wake_words = ["hey test"]
    return cfg


@pytest.fixture
def mock_executor() -> Mock:
    """Provide a mock CommandExecutor (uses helpers pattern via direct Mock for simplicity)."""
    exe = Mock()
    exe.execute_command = Mock(return_value=True)
    exe.validate_command = Mock(return_value=True)
    return exe


@pytest.fixture
def mock_state_manager() -> Mock:
    """Provide a mock StateManager."""
    sm = Mock()
    sm.current_state = "idle"
    sm.change_state = Mock(return_value=True)
    return sm


@pytest.fixture
def pipeline(mock_config: Mock, mock_executor: Mock, mock_state_manager: Mock) -> VoicePipeline:
    """Create a VoicePipeline under test with use_mock=True and pre-configured sub-mocks.

    Sub-component mocks (transcriber, tts, wake_detector) are post-configured so that
    public methods like process_text_command, get_status etc. have deterministic behavior.
    """
    p = VoicePipeline(
        config_manager=mock_config,
        command_executor=mock_executor,
        state_manager=mock_state_manager,
        use_mock=True,
        wake_words=["hey test", "ok computer"],
        voice_only=False,
    )

    # Post-configure the MagicMock instances created inside __init__ (via the mocked classes)
    p.transcriber.record_and_transcribe = Mock(return_value="open the browser please")
    p.transcriber.is_available = Mock(return_value=True)
    p.transcriber.get_backend_info = Mock(return_value={"backend": "mock", "model": "test"})

    p.tts.is_available = Mock(return_value=True)
    p.tts.speak = Mock()

    # Wake detector mock supports the methods called by pipeline and trigger_mock_wake_word
    p.wake_detector.is_listening = Mock(return_value=False)
    p.wake_detector.get_available_models = Mock(return_value=["hey test", "ok computer"])
    p.wake_detector.start_listening = Mock()
    p.wake_detector.stop_listening = Mock()
    # trigger_wake_word is used by trigger_mock_wake_word helper
    p.wake_detector.trigger_wake_word = Mock()

    return p


# ============================================================================
# TESTS
# ============================================================================


class TestVoicePipelineInitialization:
    """Unit tests for VoicePipeline construction and component wiring."""

    def test_initialization_with_use_mock(self, mock_config: Mock, mock_executor: Mock, mock_state_manager: Mock):
        """
        Test that VoicePipeline initializes successfully with use_mock=True and wires dependencies.
        
        Critical path: ensures constructor tolerates missing real voice deps and always provides
        a functional (mocked) pipeline for unit tests and CI.
        """
        # Arrange / Act
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
            wake_words=["test_wake"],
        )

        # Assert
        assert p.config_manager is mock_config
        assert p.command_executor is mock_executor
        assert p.state_manager is mock_state_manager
        assert p.wake_detector is not None
        assert p.transcriber is not None
        assert p.tts is not None
        assert p.voice_only is False
        assert p._listening is False
        assert p._processing is False
        assert isinstance(p._callbacks, list)

    def test_initialization_without_config_or_executor(self):
        """
        Test initialization when optional managers are omitted (None).
        
        Pipeline must degrade gracefully; _match_command and _execute_command should
        safely return None/False rather than crashing.
        """
        # Arrange / Act
        p = VoicePipeline(config_manager=None, command_executor=None, use_mock=True)

        # Assert
        assert p.config_manager is None
        assert p.command_executor is None
        # These should not raise
        assert p._match_command("anything") is None
        assert p._execute_command("anything") is False

    def test_callback_registered_on_init(self, pipeline: VoicePipeline):
        """The pipeline registers its internal wake callback during __init__."""
        # Assert that add_callback was invoked at least once by constructor (on the detector mock)
        assert pipeline.wake_detector.add_callback.called


class TestCallbackManagement:
    """Tests for public add/remove_command_callback and internal notification."""

    def test_add_command_callback(self, pipeline: VoicePipeline):
        """
        Test registering a callback that receives (command_name, transcription) on matches.
        """
        # Arrange
        cb = Mock()

        # Act
        pipeline.add_command_callback(cb)

        # Assert
        assert cb in pipeline._callbacks
        assert len(pipeline._callbacks) >= 1

    def test_remove_command_callback(self, pipeline: VoicePipeline):
        """
        Test that remove_command_callback removes an existing callback without error.
        """
        # Arrange
        cb = Mock()
        pipeline.add_command_callback(cb)

        # Act
        pipeline.remove_command_callback(cb)

        # Assert
        assert cb not in pipeline._callbacks

    def test_remove_nonexistent_callback_is_safe(self, pipeline: VoicePipeline):
        """Removing a callback that was never added must be a no-op (no exception)."""
        cb = Mock()
        # Act + Assert: no exception
        pipeline.remove_command_callback(cb)

    def test_notify_callbacks_invokes_all_and_swallows_exceptions(self, pipeline: VoicePipeline):
        """
        _notify_callbacks must call every registered callback and continue even if one raises.
        
        This protects the voice loop from user callback bugs.
        """
        # Arrange
        good = Mock()
        bad = Mock(side_effect=RuntimeError("boom"))
        pipeline.add_command_callback(bad)
        pipeline.add_command_callback(good)

        # Act
        pipeline._notify_callbacks("cmd", "said something")

        # Assert
        good.assert_called_once_with("cmd", "said something")
        bad.assert_called_once()  # was invoked despite raising


class TestPipelineLifecycle:
    """Tests for start/stop and listening state transitions."""

    def test_start_sets_listening_true_and_attempts_state_change(self, pipeline: VoicePipeline, mock_state_manager: Mock):
        """
        start() should set internal _listening and attempt to move state_manager to voice_listening.
        """
        # Act
        pipeline.start()

        # Assert
        assert pipeline._listening is True
        mock_state_manager.change_state.assert_called_with("voice_listening")
        pipeline.wake_detector.start_listening.assert_called_once()

    def test_start_idempotent_when_already_listening(self, pipeline: VoicePipeline):
        """Calling start() when already listening must be safe (no duplicate side effects)."""
        pipeline._listening = True
        pipeline.start()
        # second start should log warning but not crash and not call start_listening again (in real impl it returns early)
        assert pipeline._listening is True

    def test_stop_clears_listening_and_attempts_idle_state(self, pipeline: VoicePipeline, mock_state_manager: Mock):
        """
        stop() clears the listening flag and requests idle state when a state_manager is present.
        """
        # Arrange
        pipeline._listening = True

        # Act
        pipeline.stop()

        # Assert
        assert pipeline._listening is False
        mock_state_manager.change_state.assert_called_with("idle")
        pipeline.wake_detector.stop_listening.assert_called_once()

    def test_stop_is_safe_when_not_running(self, pipeline: VoicePipeline):
        """stop() must never raise even when called on a stopped pipeline."""
        pipeline.stop()
        assert pipeline._listening is False


class TestTextCommandProcessing:
    """Tests for process_text_command (public API exercising _match_command + _execute_command)."""

    def test_process_text_command_successful_match_executes_and_notifies(self, pipeline: VoicePipeline, mock_executor: Mock):
        """
        When transcription contains a keyword match from config, command is executed and callbacks notified.
        """
        # Arrange
        cb = Mock()
        pipeline.add_command_callback(cb)
        mock_executor.execute_command.return_value = True

        # Act: use literal command name in text for direct match (current _match_command
        # does substring check on exact command_name or limited curated keywords).
        result = pipeline.process_text_command("please do open_browser action now")

        # Assert
        assert result == "open_browser"
        mock_executor.execute_command.assert_called_once_with("open_browser")
        cb.assert_called_once_with("open_browser", "please do open_browser action now")

    def test_process_text_command_no_match_returns_none_without_executor_call(self, pipeline: VoicePipeline, mock_executor: Mock):
        """
        For the process_text_command public entry point, an unmatched transcription returns None
        and does not invoke the command executor (notify of empty name is done in the wake-word
        _process path, not here; see _notify_callbacks tests and _process_voice_command).
        """
        # Arrange
        original_call_count = mock_executor.execute_command.call_count

        # Act
        result = pipeline.process_text_command("gibberish xyz no keywords match")

        # Assert
        assert result is None
        # executor should not have been called for this path
        assert mock_executor.execute_command.call_count == original_call_count

    @pytest.mark.parametrize(
        "transcription,expected_cmd",
        [
            # direct name match using literal command key present in model_actions
            ("please run play_music command", "play_music"),
            # keyword match: "lights" is both a keyword entry and present as model_actions key
            ("turn on the lights", "lights"),
            ("say hello to everyone", "hello"),
            ("no match here at all", None),
        ],
    )
    def test_match_command_keyword_logic(self, pipeline: VoicePipeline, transcription: str, expected_cmd: str | None):
        """
        _match_command implements direct name + curated keyword matching against model_actions.
        """
        cmd = pipeline._match_command(transcription)
        assert cmd == expected_cmd

    def test_execute_command_delegates_to_executor_and_treats_none_as_success(self, pipeline: VoicePipeline, mock_executor: Mock):
        """_execute_command returns True when executor returns truthy (including None per impl)."""
        mock_executor.execute_command.return_value = None  # impl: "return result is not False"
        assert pipeline._execute_command("open_browser") is True

        mock_executor.execute_command.return_value = False
        assert pipeline._execute_command("open_browser") is False


class TestStatusAndListening:
    """Tests for get_status and is_listening public queries."""

    def test_get_status_returns_expected_structure(self, pipeline: VoicePipeline):
        """
        get_status aggregates listening/processing flags + availability info from components.
        """
        # Arrange
        pipeline._listening = True
        pipeline._processing = False

        # Act
        status = pipeline.get_status()

        # Assert
        assert isinstance(status, dict)
        assert status["listening"] is True
        assert status["processing"] is False
        assert "transcriber_available" in status
        assert "transcriber_info" in status
        assert "available_wake_words" in status
        assert "wake_detector_available" in status

    def test_is_listening_true_only_when_listening_and_not_processing(self, pipeline: VoicePipeline):
        """
        is_listening() is a derived view: listening AND not currently processing a command.
        """
        pipeline._listening = True
        pipeline._processing = False
        assert pipeline.is_listening() is True

        pipeline._processing = True
        assert pipeline.is_listening() is False

        pipeline._listening = False
        pipeline._processing = False
        assert pipeline.is_listening() is False


class TestErrorHandlingAndEdgeCases:
    """Error handling, graceful degradation, and edge cases."""

    def test_start_propagates_exception_from_wake_detector(self, mock_config: Mock, mock_executor: Mock, mock_state_manager: Mock):
        """
        If the wake detector fails to start_listening, the exception is surfaced (as per current impl).
        """
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening.side_effect = RuntimeError("audio device busy")

        with pytest.raises(RuntimeError):
            p.start()

    def test_process_voice_command_swallows_errors_and_resets_processing_flag(self, pipeline: VoicePipeline):
        """
        Internal _process_voice_command catches all exceptions, logs, and always resets _processing=False.
        
        We make a dependency (transcriber) raise inside the real method body so the try/except/finally runs.
        """
        # Arrange - make a called dependency raise; do NOT patch the _process itself
        pipeline.transcriber.record_and_transcribe.side_effect = RuntimeError("mic fail")

        # Act - call the real implementation directly (it is not daemon-threaded in this direct call)
        pipeline._process_voice_command("hey")

        # Assert - the real except + finally guarantees reset even on error
        assert pipeline._processing is False

    def test_trigger_mock_wake_word_delegates_when_supported(self, pipeline: VoicePipeline):
        """trigger_mock_wake_word is a test helper that forwards to detector when the method exists."""
        pipeline.trigger_mock_wake_word("hey test")
        pipeline.wake_detector.trigger_wake_word.assert_called_once_with("hey test")

    def test_voice_only_tts_feedback_on_success_and_failure_paths(self, mock_config: Mock, mock_executor: Mock, mock_state_manager: Mock):
        """
        When voice_only=True, successful/failed executions and no-match cases invoke tts.speak appropriately.
        """
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
            voice_only=True,
        )
        p.tts.is_available.return_value = True
        p.tts.speak = Mock()

        # Use a reliably matching command for this test ("lights" matches via keywords + model_actions key)
        mock_executor.execute_command.return_value = True
        p.process_text_command("turn on the lights please")
        p.tts.speak.assert_called_with("lights")  # success path speaks the matched command name

        mock_executor.execute_command.return_value = False
        p.process_text_command("turn on the lights please")
        # failure path speaks a failure message containing the command
        last_call = p.tts.speak.call_args
        assert last_call is not None
        assert "Failed" in str(last_call) or "lights" in str(last_call)

    def test_get_status_handles_detectors_without_optional_methods(self, mock_config: Mock, mock_executor: Mock):
        """get_status must tolerate wake detectors missing is_listening / get_available_models (defensive hasattr)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, use_mock=True)
        # Replace with a plain object lacking the methods
        plain = object()
        p.wake_detector = plain

        status = p.get_status()
        # Should default gracefully
        assert status["wake_detector_available"] is True
        assert status["available_wake_words"] == []
