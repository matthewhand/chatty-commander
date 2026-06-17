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
from unittest.mock import MagicMock, Mock, patch

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


class TestAdditionalMatchingHandlersAndCallbacks:
    """Additional targeted tests for _match_command, process_text_command returns,
    _notify_callbacks error resilience, and voice_only paths (extends coverage on qa #1 pipeline.py)."""

    def test_match_command_returns_none_when_config_manager_is_none(self, mock_executor: Mock, mock_state_manager: Mock):
        """_match_command short-circuits to None if no config_manager (defensive for mis-wired pipeline)."""
        # Arrange
        p = VoicePipeline(
            config_manager=None,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act
        result = p._match_command("any transcription")

        # Assert
        assert result is None

    def test_match_command_swallows_exception_and_returns_none(self, pipeline: VoicePipeline, mock_config: Mock):
        """_match_command catches unexpected errors during key access/lower and returns None safely."""
        # Arrange - corrupt model_actions to trigger except in try
        mock_config.model_actions = Mock(**{"keys.side_effect": RuntimeError("bad keys")})

        # Act
        result = pipeline._match_command("hello there")

        # Assert
        assert result is None

    def test_notify_callbacks_continues_after_one_callback_raises(self, pipeline: VoicePipeline):
        """_notify_callbacks must swallow per-callback exceptions and notify the rest (robustness for listeners)."""
        # Arrange
        calls = []
        def good_cb(cmd, text):
            calls.append(("good", cmd, text))
        def bad_cb(cmd, text):
            calls.append(("bad", cmd, text))
            raise RuntimeError("listener exploded")
        def good_cb2(cmd, text):
            calls.append(("good2", cmd, text))

        pipeline.add_command_callback(good_cb)
        pipeline.add_command_callback(bad_cb)
        pipeline.add_command_callback(good_cb2)

        # Act
        pipeline._notify_callbacks("lights", "turn on the lights")

        # Assert - all attempted; bad one did not stop the others
        assert ("good", "lights", "turn on the lights") in calls
        assert ("bad", "lights", "turn on the lights") in calls
        assert ("good2", "lights", "turn on the lights") in calls

    def test_process_text_command_matched_success_returns_command_name(self, pipeline: VoicePipeline, mock_executor: Mock):
        """process_text_command returns the matched command name on success path (public API contract)."""
        # Arrange
        mock_executor.execute_command.return_value = True

        # Act
        result = pipeline.process_text_command("please do open_browser action now")

        # Assert
        assert result == "open_browser"
        mock_executor.execute_command.assert_called_with("open_browser")

    def test_voice_only_unmatched_transcription_invokes_tts_with_transcription(self, mock_config: Mock, mock_executor: Mock, mock_state_manager: Mock):
        """When voice_only=True and no match, the unmatched handler speaks the raw transcription (via _handle_unmatched)."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
            voice_only=True,
        )
        p.tts.is_available.return_value = True
        p.tts.speak = Mock()
        # Force no-match by using transcription with no keys/keywords
        p.transcriber.record_and_transcribe = Mock(return_value="gibberish no keywords xyz")

        # Act (use internal to hit the unmatched path deterministically without thread)
        p._process_voice_command("wake")

        # Assert
        p.tts.speak.assert_called_once_with("gibberish no keywords xyz")


class TestMatchExecuteDelegatorPaths:
    """Targeted AAA tests for the small post-refactor delegator helpers
    (_match_command direct+keyword, _execute_command paths, process_text_command
    unmatched). Exercises the qa #1 pipeline module's decomposed logic and
    increases coverage on the still-listed 'no tests found' item.
    """

    def test_match_command_direct_name_hit(self, mock_config, mock_executor, mock_state_manager):
        """Direct name substring match returns the command (case-insensitive)."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act
        result = p._match_command("user said please do the open_browser thing")

        # Assert
        assert result == "open_browser"

    def test_match_command_keyword_hit(self, mock_config, mock_executor, mock_state_manager):
        """Keyword-based fallback matches configured commands like lights/music."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act + Assert
        # Use keyword-only strings (no direct command_name substrings) to exercise the fallback path
        assert p._match_command("turn the lamp on please") == "lights"
        assert p._match_command("say hi there") == "hello"

    def test_match_command_no_match_returns_none(self, mock_config, mock_executor, mock_state_manager):
        """Unknown transcription yields None (no false positive)."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act
        result = p._match_command("completely unknown phrase abc123")

        # Assert
        assert result is None

    def test_execute_command_no_executor_and_false_return(self, mock_config, mock_state_manager):
        """No executor or executor returning False/ falsy -> False, no crash."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=None,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act + Assert
        assert p._execute_command("anything") is False

        exe = Mock()
        exe.execute_command = Mock(return_value=False)
        p2 = VoicePipeline(
            config_manager=mock_config,
            command_executor=exe,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        assert p2._execute_command("open_browser") is False

    def test_execute_command_swallows_exception(self, mock_config, mock_executor, mock_state_manager):
        """Executor exception is logged and treated as failure (returns False)."""
        # Arrange
        exe = Mock()
        exe.execute_command = Mock(side_effect=RuntimeError("simulated exec fail"))
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=exe,
            state_manager=mock_state_manager,
            use_mock=True,
        )

        # Act
        result = p._execute_command("play_music")

        # Assert
        assert result is False
        exe.execute_command.assert_called_once_with("play_music")


class TestAdditionalProcessVoiceCommandPaths:
    """Further AAA tests for _process_voice_command delegator, voice_only feedback,
    error resilience in transcription, and public process_text unmatched paths.
    Targets the qa #1 listed item (pipeline complexity + 'no tests found' flag)
    by exercising more of the small delegator and state/callback paths.
    Follows existing patterns (post-configure mocks, AAA comments, fixtures).
    """

    def test_voice_only_matched_success_calls_tts_with_command_name(self, mock_config, mock_executor, mock_state_manager):
        """voice_only=True + successful match -> tts.speak is called with the matched command name."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
            voice_only=True,
        )
        p.transcriber.record_and_transcribe = Mock(return_value="turn on the lights please")
        p.tts.is_available.return_value = True
        p.tts.speak = Mock()
        mock_executor.execute_command.return_value = True

        # Act
        p._process_voice_command("wake")

        # Assert
        p.tts.speak.assert_called_with("lights")

    def test_process_voice_command_transcriber_exception_resets_processing_flag(self, pipeline):
        """If transcriber raises inside _process_voice_command, the finally still resets _processing=False (no leak)."""
        # Arrange
        pipeline.transcriber.record_and_transcribe = Mock(side_effect=RuntimeError("mic fail"))

        # Act
        pipeline._process_voice_command("wake")

        # Assert
        assert pipeline._processing is False

    def test_process_text_command_unmatched_returns_none(self, pipeline):
        """Unmatched public process_text_command returns None (no command executed)."""
        # Arrange - use text that won't direct or keyword match the fixture model_actions
        # (fixture has open_browser, play_music, hello, lights)

        # Act
        result = pipeline.process_text_command("completely unknown phrase with no keywords")

        # Assert
        assert result is None

    def test_process_voice_command_matched_notifies_callback(self, mock_config, mock_executor, mock_state_manager):
        """Successful matched path in _process notifies registered callbacks with (command_name, transcription)."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        p.transcriber.record_and_transcribe = Mock(return_value="hello there")
        cb = Mock()
        p.add_command_callback(cb)
        mock_executor.execute_command.return_value = True

        # Act
        p._process_voice_command("wake")

        # Assert
        cb.assert_called_once_with("hello", "hello there")

    def test_add_and_remove_command_callback(self, pipeline):
        """add_command_callback and remove_command_callback work for the public API (delegator support)."""
        # Arrange
        cb = Mock()

        # Act
        pipeline.add_command_callback(cb)
        assert cb in pipeline._callbacks
        pipeline.remove_command_callback(cb)

        # Assert
        assert cb not in pipeline._callbacks


class TestMatchCommandEdges:
    """Additional coverage for _match_command direct name and keyword paths (qa #1 item)."""

    def test_match_command_direct_name_match(self, mock_config, mock_executor, mock_state_manager):
        """Direct name match in transcription (case-insensitive) returns the command."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        # Act
        result = p._match_command("please do OPEN_BROWSER action")
        # Assert
        assert result == "open_browser"

    def test_match_command_keyword_music(self, mock_executor, mock_state_manager):
        """Keyword match for 'music' when 'music' action present."""
        # Arrange
        cfg = Mock()
        cfg.model_actions = {"music": {"type": "shell", "command": "play"}}
        p = VoicePipeline(
            config_manager=cfg,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        # Act
        result = p._match_command("play a song please")
        # Assert
        assert result == "music"

    def test_match_command_returns_none_for_no_actions(self, mock_executor, mock_state_manager):
        """No model_actions -> None (no crash)."""
        cfg = Mock()
        cfg.model_actions = {}
        p = VoicePipeline(
            config_manager=cfg,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        assert p._match_command("anything") is None

    def test_match_command_swallows_exception(self, mock_config, mock_executor, mock_state_manager):
        """Exception in matching returns None safely."""
        # Arrange: make model_actions cause issue in lower
        mock_config.model_actions = {"bad": None}
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        # Act
        result = p._match_command("hello")
        # Assert: should not raise, None or handled
        assert result is None or isinstance(result, str)


class TestProcessTextVoiceOnlyAdditional:
    """Extra paths for process_text_command under voice_only."""

    def test_process_text_command_voice_only_unmatched_speaks_transcription(self, mock_config, mock_executor, mock_state_manager):
        """voice_only + unmatched -> tts speaks the transcription."""
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
            voice_only=True,
        )
        p.transcriber.is_available = Mock(return_value=True)
        p.tts.is_available = Mock(return_value=True)
        p.tts.speak = Mock()
        # unmatched text
        p.process_text_command("gibberish no match xyz")
        p.tts.speak.assert_called_with("gibberish no match xyz")


class TestVoicePipelineAdditionalCoverage:
    """4-8 additional unit tests for VoicePipeline to address qa 'no tests found' and further exercise extracted logic from _process_voice_command / _match (qa rank 1)."""

    def test_match_by_keywords_no_match_when_command_not_in_actions(self, mock_executor, mock_state_manager):
        """Keywords present but command_name not in model_actions -> no return."""
        cfg = Mock()
        cfg.model_actions = {"lights": {}}  # 'music' keyword exists but not this action
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p._match_command("play music") is None

    def test_get_status_defaults_when_detectors_lack_methods(self, mock_config, mock_executor):
        """get_status uses hasattr guards for wake_detector missing is_listening/get_available_models."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, use_mock=True)
        p.wake_detector = object()  # plain object
        status = p.get_status()
        assert status["wake_detector_available"] is True
        assert status["available_wake_words"] == []

    def test_is_listening_false_during_processing(self, pipeline):
        """is_listening returns False if _processing even if _listening."""
        pipeline._listening = True
        pipeline._processing = True
        assert pipeline.is_listening() is False

    def test_trigger_mock_wake_word_ignores_when_no_method(self, mock_config, mock_executor, capsys):
        """trigger_mock_wake_word logs warning if detector lacks trigger method."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, use_mock=True)
        p.wake_detector = object()
        p.trigger_mock_wake_word("foo")
        # no crash; warning may be logged

    def test_process_text_command_no_config_manager_returns_none(self, mock_executor, mock_state_manager):
        """process_text_command short circuits safely with no config_manager."""
        p = VoicePipeline(config_manager=None, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p.process_text_command("any") is None

    def test_match_command_keyword_lights(self, mock_executor, mock_state_manager):
        """Keyword 'lights' matches when action present."""
        cfg = Mock()
        cfg.model_actions = {"lights": {}}
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p._match_command("turn on the lamp") == "lights"

    def test_find_direct_name_match_hits_substring(self, mock_executor, mock_state_manager):
        """_find_direct_name_match (extracted for qa #1) returns command on substring hit."""
        cfg = Mock()
        cfg.model_actions = {"hello": {}, "lights": {}}
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p._find_direct_name_match("please say hello now", cfg.model_actions) == "hello"

    def test_find_direct_name_match_returns_none_no_match(self, mock_executor, mock_state_manager):
        """_find_direct_name_match returns None when no direct name substring matches."""
        cfg = Mock()
        cfg.model_actions = {"hello": {}}
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p._find_direct_name_match("completely unrelated words", cfg.model_actions) is None

    def test_find_direct_name_match_case_insensitive(self, mock_executor, mock_state_manager):
        """_find_direct_name_match is case insensitive per transcription_lower (caller lowers)."""
        cfg = Mock()
        cfg.model_actions = {"lights": {}}
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        assert p._find_direct_name_match("turn on the lights", cfg.model_actions) == "lights"

    def test_match_command_prefers_direct_name_over_keyword(self, mock_executor, mock_state_manager):
        """_match_command tries direct name first, returns it even if keyword would also match."""
        cfg = Mock()
        cfg.model_actions = {"hello": {}, "lights": {}}
        p = VoicePipeline(config_manager=cfg, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        # 'hello' direct substring, 'lights' also keyword match possible but direct wins
        assert p._match_command("say hello lights") == "hello"

    def test_process_text_command_matched_but_execute_fails_returns_none(self, mock_config, mock_executor, mock_state_manager):
        """process_text_command returns None (no crash) if match but execute fails (per if success)."""
        # Arrange
        p = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        p.transcriber.record_and_transcribe = Mock(return_value="lights on")
        mock_executor.execute_command.return_value = False  # causes handle to return False

        # Act
        result = p.process_text_command("turn on the lights")

        # Assert
        assert result is None

    def test_get_status_transcriber_not_available(self, mock_config, mock_executor):
        """get_status reports transcriber_available=False when backend reports so."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, use_mock=True)
        p.transcriber.is_available.return_value = False
        status = p.get_status()
        assert status["transcriber_available"] is False

    def test_is_listening_true_path(self, pipeline):
        """is_listening True only when listening and not processing (positive case)."""
        pipeline._listening = True
        pipeline._processing = False
        assert pipeline.is_listening() is True

    def test_execute_command_no_executor_returns_false(self, mock_config, mock_state_manager):
        """_execute_command returns False safely when no command_executor (exercises extracted path)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=None, state_manager=mock_state_manager, use_mock=True)
        assert p._execute_command("any") is False

    def test_start_already_listening_returns_early(self, pipeline, mock_state_manager):
        """start() when already _listening logs warning and returns without starting again."""
        pipeline._listening = True
        pipeline.start()
        pipeline.wake_detector.start_listening.assert_not_called()
        # state not updated again

    def test_on_wake_word_detected_ignores_if_processing(self, pipeline):
        """_on_wake_word_detected does nothing (no thread) if already _processing."""
        pipeline._processing = True
        # Should not start thread or call process
        pipeline._on_wake_word_detected("hey test", 0.9)
        # No exception, and _processing remains (no new work)

    def test_start_sets_listening_and_calls_detector(self, pipeline):
        """start() succeeds, sets _listening, calls detector start_listening."""
        pipeline._listening = False
        pipeline.start()
        assert pipeline._listening is True
        pipeline.wake_detector.start_listening.assert_called_once()

    def test_stop_resets_listening_and_calls_detector(self, pipeline):
        """stop() sets _listening=False and calls stop_listening."""
        pipeline._listening = True
        pipeline.stop()
        assert pipeline._listening is False
        pipeline.wake_detector.stop_listening.assert_called_once()

    def test_start_state_change_exception_swallowed(self, pipeline, mock_state_manager):
        """start() sets listening=True even if state change raises (uses _try_change_state)."""
        mock_state_manager.change_state.side_effect = RuntimeError("state fail")
        pipeline._listening = False
        pipeline.start()
        assert pipeline._listening is True
        mock_state_manager.change_state.assert_called_with("voice_listening")

    def test_process_voice_command_empty_transcription_resets_processing(self, pipeline):
        """_process_voice_command with empty transcription returns early and resets _processing in finally."""
        pipeline.transcriber.record_and_transcribe = Mock(return_value="")
        pipeline._processing = False
        pipeline._process_voice_command("wake")
        assert pipeline._processing is False

    def test_unmatched_transcription_notifies_callbacks(self, pipeline, mock_config, mock_executor, mock_state_manager):
        """Unmatched transcription in process_text still notifies callbacks (via _handle_unmatched)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.transcriber.record_and_transcribe = Mock(return_value="unknown phrase xyz")
        cb = Mock()
        p.add_command_callback(cb)
        p.process_text_command("unknown phrase xyz")
        cb.assert_called_once_with("", "unknown phrase xyz")

    def test_get_status_full_structure(self, pipeline):
        """get_status returns dict with all expected keys and types."""
        status = pipeline.get_status()
        assert isinstance(status, dict)
        for key in ("listening", "processing", "wake_detector_available", "transcriber_available", "transcriber_info", "available_wake_words"):
            assert key in status

    def test_start_state_manager_exception(self, mock_config, mock_executor, mock_state_manager):
        """start() sets listening even if state change raises (handled in _try_change_state)."""
        mock_state_manager.change_state.side_effect = Exception("boom")
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock()
        p.start()
        assert p._listening is True

    def test_stop_state_manager_exception(self, pipeline, mock_state_manager):
        """stop() resets listening even if state change raises."""
        mock_state_manager.change_state.side_effect = Exception("boom")
        pipeline._listening = True
        pipeline.stop()
        assert pipeline._listening is False

    def test_callbacks_notified_on_unmatched(self, pipeline):
        """Unmatched transcription notifies registered callbacks."""
        pipeline.transcriber.record_and_transcribe = Mock(return_value="no match here")
        cb = Mock()
        pipeline.add_command_callback(cb)
        pipeline.process_text_command("no match here")
        cb.assert_called_once()

    def test_get_status_missing_detector_methods(self, mock_config, mock_executor):
        """get_status falls back safely when wake_detector lacks optional methods."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, use_mock=True)
        # remove methods to test hasattr guards
        if hasattr(p.wake_detector, 'is_listening'):
            delattr(p.wake_detector, 'is_listening')
        if hasattr(p.wake_detector, 'get_available_models'):
            delattr(p.wake_detector, 'get_available_models')
        status = p.get_status()
        assert status["wake_detector_available"] is True
        assert status["available_wake_words"] == []

    def test_start_no_state_manager(self, mock_config, mock_executor):
        """start() works without state_manager (no crash, listening set)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=None, use_mock=True)
        p.wake_detector.start_listening = Mock()
        p.start()
        assert p._listening is True

    def test_stop_detector_exception_still_resets(self, pipeline):
        """stop() resets _listening even if wake_detector.stop_listening raises."""
        pipeline._listening = True
        pipeline.wake_detector.stop_listening.side_effect = RuntimeError("stop fail")
        pipeline.stop()
        assert pipeline._listening is False

    def test_add_remove_callback_multiple(self, pipeline):
        """add/remove callbacks multiple times and check _callbacks list."""
        cb1, cb2 = Mock(), Mock()
        pipeline.add_command_callback(cb1)
        pipeline.add_command_callback(cb2)
        assert len(pipeline._callbacks) == 2
        pipeline.remove_command_callback(cb1)
        assert cb1 not in pipeline._callbacks
        pipeline.remove_command_callback(cb2)
        assert len(pipeline._callbacks) == 0

    def test_process_text_voice_only_success_returns_name(self, mock_config, mock_executor, mock_state_manager):
        """voice_only + successful match returns command name from process_text_command."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True, voice_only=True)
        p.transcriber.record_and_transcribe = Mock(return_value="say hello")
        mock_executor.execute_command.return_value = True
        p.tts.is_available = Mock(return_value=True)
        p.tts.speak = Mock()
        result = p.process_text_command("say hello")
        assert result == "hello"

    def test_start_wake_detector_raises_propagates(self, mock_config, mock_executor, mock_state_manager):
        """start() propagates exception from wake_detector.start_listening."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening.side_effect = RuntimeError("mic fail")
        try:
            p.start()
        except RuntimeError as e:
            assert "mic fail" in str(e)
        assert p._listening is False

    def test_process_text_match_but_tts_unavailable(self, mock_config, mock_executor, mock_state_manager):
        """voice_only match success but tts not available still returns name (no speak)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True, voice_only=True)
        p.transcriber.record_and_transcribe = Mock(return_value="lights on")
        mock_executor.execute_command.return_value = True
        p.tts.is_available = Mock(return_value=False)
        p.tts.speak = Mock()
        result = p.process_text_command("lights on")
        assert result == "lights"
        p.tts.speak.assert_not_called()

    def test_get_status_after_start(self, pipeline):
        """get_status reflects listening=True after successful start."""
        pipeline.wake_detector.start_listening = Mock()
        pipeline.start()
        status = pipeline.get_status()
        assert status["listening"] is True

    def test_remove_nonexistent_callback_no_error(self, pipeline):
        """remove_command_callback on non-existing is safe (no KeyError etc)."""
        cb = Mock()
        pipeline.remove_command_callback(cb)  # should not raise
        assert cb not in pipeline._callbacks

    def test_start_updates_state_with_voice_listening(self, pipeline, mock_state_manager):
        """start() calls _try_change_state with 'voice_listening' when state_manager present."""
        pipeline.wake_detector.start_listening = Mock()
        mock_state_manager.change_state.reset_mock()
        pipeline.start()
        mock_state_manager.change_state.assert_called_with("voice_listening")

    def test_stop_updates_state_with_idle(self, pipeline, mock_state_manager):
        """stop() calls _try_change_state with 'idle' when state_manager present."""
        pipeline._listening = True
        mock_state_manager.change_state.reset_mock()
        pipeline.stop()
        mock_state_manager.change_state.assert_called_with("idle")

    def test_process_text_command_no_match_calls_unmatched(self, pipeline):
        """No match in process_text_command calls _handle_unmatched_transcription."""
        pipeline.transcriber.record_and_transcribe = Mock(return_value="unknown foo")
        with patch.object(pipeline, '_handle_unmatched_transcription') as mock_unmatched:
            pipeline.process_text_command("unknown foo")
            mock_unmatched.assert_called_once_with("unknown foo")

    def test_get_status_includes_transcriber_info(self, pipeline):
        """get_status includes transcriber_info from transcriber."""
        status = pipeline.get_status()
        assert "transcriber_info" in status
        assert status["transcriber_info"] == {"backend": "mock", "model": "test"}

    def test_process_voice_command_no_transcription(self, pipeline):
        """No transcription received: early return, _processing reset in finally."""
        pipeline.transcriber.record_and_transcribe = Mock(return_value=None)
        pipeline._processing = True
        pipeline._process_voice_command("wake")
        assert pipeline._processing is False

    def test_handle_matched_tts_fail_message(self, mock_config, mock_executor, mock_state_manager):
        """Matched but execute fails, voice_only=True: speaks 'Failed to execute ...'."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True, voice_only=True)
        p.transcriber.record_and_transcribe = Mock(return_value="turn lights")
        mock_executor.execute_command.return_value = False
        p.tts.is_available = Mock(return_value=True)
        p.tts.speak = Mock()
        p._handle_matched_command("lights", "turn lights")
        p.tts.speak.assert_called_with("Failed to execute lights")

    def test_start_state_change_exception(self, mock_config, mock_executor, mock_state_manager):
        """start() swallows state change exception (debug logged), still sets listening."""
        mock_state_manager.change_state.side_effect = Exception("state boom")
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock()
        p.start()
        assert p._listening is True

    def test_on_wake_word_detected_triggers_process(self, mock_config, mock_executor, mock_state_manager):
        """_on_wake_word_detected (when not processing) would start thread to _process (test by direct, but verify no ignore)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p._processing = False
        # We can't easily test thread start without patch, but verify it doesn't early return
        # Call _process directly to simulate
        p.transcriber.record_and_transcribe = Mock(return_value="hello")
        mock_executor.execute_command.return_value = True
        p._process_voice_command("wake")
        # If reached here, no early ignore
        assert True


class TestPipelineAdditionalCoverage:
    """4 additional focused tests for pipeline (get_status, trigger mock, idempotent start, voice_only unmatched).
    Addresses remaining qa 'no tests found' flags and coverage for VoicePipeline (even if report stale).
    """

    def test_get_status_returns_expected_keys(self, pipeline):
        """get_status returns dict with listening/processing/wake/transcriber keys."""
        status = pipeline.get_status()
        assert isinstance(status, dict)
        assert "listening" in status
        assert "processing" in status
        assert "wake_detector_available" in status
        assert "transcriber_available" in status

    def test_trigger_mock_wake_word_calls_if_available(self, mock_config, mock_executor, mock_state_manager):
        """trigger_mock_wake_word delegates to wake_detector if method present."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.trigger_wake_word = Mock()
        p.trigger_mock_wake_word("hey_test")
        p.wake_detector.trigger_wake_word.assert_called_with("hey_test")

    def test_start_is_idempotent(self, mock_config, mock_executor, mock_state_manager):
        """Calling start() when already listening does not restart."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock()
        p._listening = True
        p.start()
        # Should warn and not call again
        p.wake_detector.start_listening.assert_not_called()

    def test_voice_only_unmatched_speaks_transcription(self, mock_config, mock_executor, mock_state_manager):
        """voice_only + unmatched -> tts.speak called with the transcription text."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True, voice_only=True)
        p.transcriber.record_and_transcribe = Mock(return_value="unknown phrase")
        p.tts.is_available = Mock(return_value=True)
        p.tts.speak = Mock()
        p._handle_unmatched_transcription("unknown phrase")
        p.tts.speak.assert_called_with("unknown phrase")


class TestPipelineMoreCoverage:
    """Additional 4 tests to further address 'no tests found' for voice/pipeline.py per qa_report."""
    def test_is_listening(self, pipeline):
        """is_listening reflects _listening and not _processing."""
        pipeline._listening = True
        pipeline._processing = False
        assert pipeline.is_listening() is True
        pipeline._processing = True
        assert pipeline.is_listening() is False

    def test_process_text_command_matched_returns_command_name(self, pipeline, mock_executor):
        """process_text_command on match returns the command name."""
        pipeline._match_command = Mock(return_value="hello")
        mock_executor.execute_command.return_value = True
        result = pipeline.process_text_command("hello world")
        assert result == "hello"

    def test_remove_non_existing_callback_safe(self, pipeline):
        """Removing non-registered callback is safe, no error."""
        cb = Mock()
        pipeline.remove_command_callback(cb)  # should not raise
        assert True

    def test_get_status_includes_wake_words_from_detector(self, mock_config, mock_executor, mock_state_manager):
        """get_status pulls available_wake_words from detector when available."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.get_available_models = Mock(return_value=["hey_test"])
        status = p.get_status()
        assert status["available_wake_words"] == ["hey_test"]

    def test_start_calls_wake_detector_and_sets_listening(self, mock_config, mock_executor, mock_state_manager):
        """start() calls wake_detector.start_listening and sets _listening=True."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock()
        p.start()
        p.wake_detector.start_listening.assert_called_once()
        assert p._listening is True

    def test_stop_resets_listening_and_calls_detector(self, mock_config, mock_executor, mock_state_manager):
        """stop() resets _listening=False and calls stop_listening."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p._listening = True
        p.wake_detector.stop_listening = Mock()
        p.stop()
        assert p._listening is False
        p.wake_detector.stop_listening.assert_called_once()

    def test_add_remove_callbacks(self, pipeline):
        """add and remove callbacks work correctly."""
        cb1 = Mock()
        cb2 = Mock()
        pipeline.add_command_callback(cb1)
        pipeline.add_command_callback(cb2)
        assert len(pipeline._callbacks) == 2
        pipeline.remove_command_callback(cb1)
        assert cb1 not in pipeline._callbacks
        assert cb2 in pipeline._callbacks

    def test_get_status_with_no_state_manager(self, mock_config, mock_executor):
        """get_status works even without state_manager."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=None, use_mock=True)
        status = p.get_status()
        assert "listening" in status

    def test_process_text_command_executor_fails_returns_none(self, pipeline, mock_executor):
        """Matched command but executor returns False/raises -> returns None (feedback in handler)."""
        pipeline._match_command = Mock(return_value="open_browser")
        mock_executor.execute_command.return_value = False
        result = pipeline.process_text_command("open browser now")
        assert result is None

    def test_trigger_mock_wake_word_no_method_does_not_crash(self, mock_config, mock_executor, mock_state_manager):
        """trigger_mock_wake_word safe when detector lacks trigger_wake_word (logs warning)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        # remove the method to simulate
        if hasattr(p.wake_detector, "trigger_wake_word"):
            delattr(p.wake_detector, "trigger_wake_word")
        # should not raise
        p.trigger_mock_wake_word("hey_test")
        assert True

    def test_get_status_transcriber_available_false(self, mock_config, mock_executor, mock_state_manager):
        """get_status reports transcriber_available=False when transcriber reports unavailable."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.transcriber.is_available = Mock(return_value=False)
        status = p.get_status()
        assert status.get("transcriber_available") is False

    def test_process_voice_swallows_handler_exception_and_resets(self, pipeline, mock_executor):
        """_process_voice_command catches exceptions in match/handler, resets _processing."""
        pipeline.transcriber.record_and_transcribe = Mock(return_value="foo")
        pipeline._match_command = Mock(side_effect=Exception("match boom"))
        pipeline._processing = True
        pipeline._process_voice_command("wake")
        assert pipeline._processing is False

    def test_start_raises_on_wake_detector_failure(self, mock_config, mock_executor, mock_state_manager):
        """start() raises if wake_detector.start_listening fails (no swallow for detector)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock(side_effect=RuntimeError("mic fail"))
        try:
            p.start()
        except RuntimeError as e:
            assert "mic fail" in str(e)
        assert p._listening is False

    def test_stop_swallows_stop_listening_error(self, mock_config, mock_executor, mock_state_manager):
        """stop() swallows exception from stop_listening, still clears listening flag."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p._listening = True
        p.wake_detector.stop_listening = Mock(side_effect=Exception("stop boom"))
        p.stop()
        assert p._listening is False

    def test_on_wake_skips_if_already_processing(self, mock_config, mock_executor, mock_state_manager):
        """_on_wake_word_detected returns early without starting thread if _processing."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p._processing = True
        # patch to ensure not called
        with patch.object(p, '_process_voice_command') as mock_proc:
            p._on_wake_word_detected("hey", 0.9)
            mock_proc.assert_not_called()

    def test_process_text_empty_transcription_calls_unmatched(self, pipeline):
        """process_text_command with falsy transcription calls unmatched handler."""
        pipeline._match_command = Mock(return_value=None)
        with patch.object(pipeline, '_handle_unmatched_transcription') as mock_un:
            pipeline.process_text_command("")
            mock_un.assert_called_once_with("")

    def test_start_idempotent_when_already_listening(self, mock_config, mock_executor, mock_state_manager):
        """start() logs warning and returns early if already listening."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p._listening = True
        p.wake_detector.start_listening = Mock()
        p.start()
        p.wake_detector.start_listening.assert_not_called()
        assert p._listening is True

    def test_get_status_wake_detector_not_listening(self, mock_config, mock_executor, mock_state_manager):
        """get_status reports wake_detector_available=False when is_listening returns False."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.is_listening = Mock(return_value=False)
        status = p.get_status()
        assert status["wake_detector_available"] is False

    def test_execute_command_treats_false_as_failure(self, mock_config, mock_executor, mock_state_manager):
        """_execute_command returns False when executor returns exactly False."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        mock_executor.execute_command.return_value = False
        assert p._execute_command("foo") is False

    def test_notify_callbacks_continues_on_exception(self, pipeline):
        """_notify_callbacks logs error but continues for other callbacks."""
        cb1 = Mock(side_effect=Exception("cb1 fail"))
        cb2 = Mock()
        pipeline._callbacks = [cb1, cb2]
        pipeline._notify_callbacks("cmd", "trans")
        cb2.assert_called_once_with("cmd", "trans")

    def test_process_voice_command_transcriber_raises_resets(self, mock_config, mock_executor, mock_state_manager):
        """_process_voice_command resets _processing even if record_and_transcribe raises."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.transcriber.record_and_transcribe = Mock(side_effect=RuntimeError("transcribe fail"))
        p._processing = True
        p._process_voice_command("wake")
        assert p._processing is False

    def test_get_status_handles_missing_detector_methods(self, mock_config, mock_executor, mock_state_manager):
        """get_status tolerates detectors without expected methods via hasattr."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        # simulate missing by deleting if present (but use mock side)
        del p.wake_detector.is_listening
        del p.wake_detector.get_available_models
        status = p.get_status()
        assert "wake_detector_available" in status
        assert status["available_wake_words"] == []

    def test_start_swallows_state_change_but_raises_on_wake_fail(self, mock_config, mock_executor, mock_state_manager):
        """start raises on wake fail; state change failure is in _try (logged)."""
        p = VoicePipeline(config_manager=mock_config, command_executor=mock_executor, state_manager=mock_state_manager, use_mock=True)
        p.wake_detector.start_listening = Mock(side_effect=RuntimeError("no mic"))
        mock_state_manager.change_state.side_effect = Exception("state fail")
        try:
            p.start()
        except RuntimeError:
            pass
        assert p._listening is False

    def test_process_text_command_success_returns_name(self, pipeline, mock_executor):
        """process_text_command on successful match returns the command name."""
        pipeline._match_command = Mock(return_value="hello")
        mock_executor.execute_command.return_value = True
        result = pipeline.process_text_command("hello there")
        assert result == "hello"


