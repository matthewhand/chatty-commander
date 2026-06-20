# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.

"""Branch-coverage tests for ``chatty_commander.voice.pipeline``.

These tests exercise the uncovered paths of :class:`VoicePipeline`:
construction with mocked components, the full ``_process_voice_command``
flow with synthetic transcriptions, error handling in start/stop/dispatch,
state-manager update branches, TTS feedback branches, and lifecycle helpers.

All external/audio dependencies are mocked at the boundary (the transcriber,
TTS, and wakeword detector) so the tests are fast and hermetic.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from chatty_commander.voice.pipeline import VoicePipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_pipeline(**kwargs) -> VoicePipeline:
    """Build a pipeline forced onto mock components.

    With ``use_mock=True`` the wakeword detector is a ``MockWakeWordDetector``
    and the transcription backend is forced to ``"mock"`` and the TTS backend
    is whatever is passed (defaults to a mock-friendly backend via patching in
    individual tests).
    """
    kwargs.setdefault("use_mock", True)
    return VoicePipeline(**kwargs)


def install_fake_io(pipeline: VoicePipeline, *, transcription="", tts_available=True):
    """Replace transcriber and tts with controllable mocks."""
    pipeline.transcriber = Mock()
    pipeline.transcriber.record_and_transcribe.return_value = transcription
    pipeline.transcriber.is_available.return_value = True
    pipeline.transcriber.get_backend_info.return_value = {"backend": "mock"}

    pipeline.tts = Mock()
    pipeline.tts.is_available.return_value = tts_available
    return pipeline


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construction_uses_mock_components():
    pipeline = make_pipeline(wake_words=["hey_jarvis"])
    # Mock wake detector exposes trigger_wake_word.
    assert hasattr(pipeline.wake_detector, "trigger_wake_word")
    assert pipeline._listening is False
    assert pipeline._processing is False
    assert pipeline._callbacks == []
    # The wake detector should have our internal handler registered.
    assert pipeline.wake_detector._callbacks  # type: ignore[attr-defined]


def test_construction_real_path_when_deps_available(monkeypatch):
    """When VOICE_DEPS_AVAILABLE and not use_mock, real WakeWordDetector is built.

    We stub WakeWordDetector/VoiceTranscriber/TextToSpeech so no audio stack is
    touched, then assert the non-mock branch (line 73) is taken.
    """
    import chatty_commander.voice.pipeline as mod

    fake_detector = Mock()
    fake_detector_cls = Mock(return_value=fake_detector)
    monkeypatch.setattr(mod, "VOICE_DEPS_AVAILABLE", True)
    monkeypatch.setattr(mod, "WakeWordDetector", fake_detector_cls)
    monkeypatch.setattr(mod, "VoiceTranscriber", Mock(return_value=Mock()))
    monkeypatch.setattr(mod, "TextToSpeech", Mock(return_value=Mock()))

    pipeline = VoicePipeline(use_mock=False, wake_words=["x"])

    fake_detector_cls.assert_called_once()
    assert pipeline.wake_detector is fake_detector
    fake_detector.add_callback.assert_called_once()


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def test_add_and_remove_command_callback():
    pipeline = make_pipeline()

    def cb(name, txt):  # pragma: no cover - body not invoked here
        return None

    pipeline.add_command_callback(cb)
    assert cb in pipeline._callbacks
    pipeline.remove_command_callback(cb)
    assert cb not in pipeline._callbacks
    # Removing again is a no-op (covers the guarded branch).
    pipeline.remove_command_callback(cb)


def test_notify_callbacks_swallows_exceptions():
    pipeline = make_pipeline()
    good = Mock()
    bad = Mock(side_effect=RuntimeError("boom"))
    pipeline.add_command_callback(bad)
    pipeline.add_command_callback(good)
    # Should not raise even though one callback errors.
    pipeline._notify_callbacks("hello", "hello there")
    good.assert_called_once_with("hello", "hello there")


# ---------------------------------------------------------------------------
# start / stop lifecycle
# ---------------------------------------------------------------------------


def test_start_sets_listening_and_updates_state():
    state = Mock()
    pipeline = make_pipeline(state_manager=state)
    pipeline.wake_detector = Mock()
    pipeline.start()
    assert pipeline._listening is True
    state.change_state.assert_called_with("voice_listening")


def test_start_when_already_listening_warns_and_returns():
    pipeline = make_pipeline()
    pipeline.wake_detector = Mock()
    pipeline._listening = True
    pipeline.start()
    # Detector should never be told to start again.
    pipeline.wake_detector.start_listening.assert_not_called()


def test_start_state_update_failure_is_swallowed():
    state = Mock()
    state.change_state.side_effect = RuntimeError("nope")
    pipeline = make_pipeline(state_manager=state)
    pipeline.wake_detector = Mock()
    # Should not raise despite state error.
    pipeline.start()
    assert pipeline._listening is True


def test_start_detector_failure_reraises():
    pipeline = make_pipeline()
    pipeline.wake_detector = Mock()
    pipeline.wake_detector.start_listening.side_effect = RuntimeError("hw fail")
    with pytest.raises(RuntimeError):
        pipeline.start()


def test_stop_updates_state_idle():
    state = Mock()
    pipeline = make_pipeline(state_manager=state)
    pipeline.wake_detector = Mock()
    pipeline._listening = True
    pipeline.stop()
    assert pipeline._listening is False
    state.change_state.assert_called_with("idle")


def test_stop_state_update_failure_swallowed():
    state = Mock()
    state.change_state.side_effect = RuntimeError("nope")
    pipeline = make_pipeline(state_manager=state)
    pipeline.wake_detector = Mock()
    pipeline.stop()
    assert pipeline._listening is False


def test_stop_detector_failure_swallowed():
    pipeline = make_pipeline()
    pipeline.wake_detector = Mock()
    pipeline.wake_detector.stop_listening.side_effect = RuntimeError("boom")
    # Should not raise.
    pipeline.stop()
    assert pipeline._listening is False


# ---------------------------------------------------------------------------
# _on_wake_word_detected dispatch
# ---------------------------------------------------------------------------


def test_on_wake_word_ignored_when_processing():
    pipeline = make_pipeline()
    pipeline._processing = True
    called = {}
    pipeline._process_voice_command = lambda w: called.setdefault("x", w)  # type: ignore
    pipeline._on_wake_word_detected("hey", 0.99)
    assert called == {}


def test_on_wake_word_spawns_processing_thread(monkeypatch):
    pipeline = make_pipeline()
    seen = {}

    def fake_process(wake_word):
        seen["wake_word"] = wake_word

    pipeline._process_voice_command = fake_process  # type: ignore

    # Run the spawned thread synchronously by stubbing Thread.
    import chatty_commander.voice.pipeline as mod

    class ImmediateThread:
        def __init__(self, target, args, daemon):
            self._target = target
            self._args = args

        def start(self):
            self._target(*self._args)

    monkeypatch.setattr(mod.threading, "Thread", ImmediateThread)
    pipeline._on_wake_word_detected("hey_jarvis", 0.5)
    assert seen["wake_word"] == "hey_jarvis"


def test_two_rapid_wake_words_start_only_one_processing_run():
    """Two wake words arriving back-to-back must result in exactly one
    processing run: the check-and-set of ``_processing`` is guarded by a lock,
    so the second detection sees the slot already claimed and is ignored.

    The first worker is held inside ``_process_voice_command`` (via a barrier)
    until *after* the second detection has been delivered, reproducing the
    race window where both could otherwise pass the guard.
    """
    import threading as _threading

    pipeline = make_pipeline()

    started = []
    proceed = _threading.Event()
    entered = _threading.Event()

    def blocking_process(wake_word):
        started.append(wake_word)
        entered.set()
        # Hold the processing slot open until the test releases us.
        proceed.wait(timeout=2.0)
        # Mirror real behaviour: clear the flag in a finally-equivalent.
        pipeline._processing = False

    pipeline._process_voice_command = blocking_process  # type: ignore

    # First detection spawns a real daemon thread and claims the slot.
    pipeline._on_wake_word_detected("hey_jarvis", 0.9)
    assert entered.wait(timeout=2.0), "first worker never started"

    # Second detection arrives while the first still holds the slot.
    pipeline._on_wake_word_detected("hey_jarvis", 0.9)

    # Release the first worker and let it finish.
    proceed.set()
    if pipeline._processing_thread is not None:
        pipeline._processing_thread.join(timeout=2.0)

    # Exactly one processing run despite two detections.
    assert started == ["hey_jarvis"]
    assert pipeline._processing is False


# ---------------------------------------------------------------------------
# _process_voice_command flow
# ---------------------------------------------------------------------------


def test_process_no_transcription_returns_early():
    state = Mock()
    pipeline = make_pipeline(state_manager=state)
    install_fake_io(pipeline, transcription="")
    cb = Mock()
    pipeline.add_command_callback(cb)
    pipeline._process_voice_command("hey")
    cb.assert_not_called()
    assert pipeline._processing is False
    # Final state returns to listening.
    state.change_state.assert_called_with("voice_listening")


def test_process_matched_command_success_notifies_and_speaks():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = True
    state = Mock()
    pipeline = make_pipeline(
        config_manager=config,
        command_executor=executor,
        state_manager=state,
        voice_only=True,
    )
    install_fake_io(pipeline, transcription="hello there")
    cb = Mock()
    pipeline.add_command_callback(cb)

    pipeline._process_voice_command("hey")

    executor.execute_command.assert_called_once_with("hello")
    cb.assert_called_once_with("hello", "hello there")
    pipeline.tts.speak.assert_called_once_with("hello")


def test_process_matched_command_failure_speaks_failure():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = False
    pipeline = make_pipeline(
        config_manager=config,
        command_executor=executor,
        voice_only=True,
    )
    install_fake_io(pipeline, transcription="hello there")
    cb = Mock()
    pipeline.add_command_callback(cb)

    pipeline._process_voice_command("hey")

    cb.assert_not_called()
    pipeline.tts.speak.assert_called_once_with("Failed to execute hello")


def test_process_no_match_notifies_empty_and_speaks_apology():
    config = Mock()
    config.model_actions = {"hello": {}}
    pipeline = make_pipeline(config_manager=config, voice_only=True)
    install_fake_io(pipeline, transcription="banana split")
    cb = Mock()
    pipeline.add_command_callback(cb)

    pipeline._process_voice_command("hey")

    cb.assert_called_once_with("", "banana split")
    pipeline.tts.speak.assert_called_once_with("Sorry, I didn't understand that")


def test_process_recording_exception_swallowed():
    state = Mock()
    pipeline = make_pipeline(state_manager=state)
    install_fake_io(pipeline)
    pipeline.transcriber.record_and_transcribe.side_effect = RuntimeError("mic")
    # Should not raise; processing flag reset in finally.
    pipeline._process_voice_command("hey")
    assert pipeline._processing is False


def test_process_state_update_failures_swallowed_throughout():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = True
    state = Mock()
    state.change_state.side_effect = RuntimeError("state down")
    pipeline = make_pipeline(
        config_manager=config,
        command_executor=executor,
        state_manager=state,
    )
    install_fake_io(pipeline, transcription="hello there")
    # All state.change_state calls raise but the flow completes.
    pipeline._process_voice_command("hey")
    executor.execute_command.assert_called_once_with("hello")
    assert pipeline._processing is False


def test_process_not_voice_only_skips_tts():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = True
    pipeline = make_pipeline(
        config_manager=config, command_executor=executor, voice_only=False
    )
    install_fake_io(pipeline, transcription="hello there")
    pipeline._process_voice_command("hey")
    pipeline.tts.speak.assert_not_called()


# ---------------------------------------------------------------------------
# _match_command
# ---------------------------------------------------------------------------


def test_match_command_no_config_manager():
    pipeline = make_pipeline()
    assert pipeline._match_command("hello") is None


def test_match_command_empty_model_actions():
    config = Mock()
    config.model_actions = {}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("hello") is None


def test_match_command_direct_whole_word():
    config = Mock()
    config.model_actions = {"hello": {}}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("please say hello now") == "hello"


def test_match_command_avoids_substring_false_positive():
    config = Mock()
    config.model_actions = {"play": {}}
    pipeline = make_pipeline(config_manager=config)
    # "replay" should NOT match the single-word command "play".
    assert pipeline._match_command("replay that") is None


def test_match_command_multiword_phrase():
    config = Mock()
    config.model_actions = {"turn on": {}}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("please turn on the fan") == "turn on"
    assert pipeline._match_command("turn the fan on") is None


def test_match_command_keyword_fallback():
    config = Mock()
    config.model_actions = {"lights": {}}
    pipeline = make_pipeline(config_manager=config)
    # "lamp" is a keyword for "lights"; direct name "lights" not in transcript.
    assert pipeline._match_command("switch on the lamp") == "lights"


def test_match_command_empty_command_name_skipped():
    config = Mock()
    # An empty / whitespace-only command name exercises the early-return at
    # line 249 (phrase is empty after strip).
    config.model_actions = {"   ": {}, "hello": {}}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("say hello") == "hello"


def test_match_command_punctuation_only_name_skipped():
    config = Mock()
    # A punctuation-only command name has no alphanumeric tokens, exercising
    # the early-return at line 252.
    config.model_actions = {"!!!": {}, "hello": {}}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("say hello") == "hello"
    # And when nothing matches, returns None.
    assert pipeline._match_command("!!!") is None


def test_match_command_no_match_returns_none():
    config = Mock()
    config.model_actions = {"hello": {}}
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("xyzzy") is None


def test_match_command_handles_internal_exception():
    config = Mock()
    # model_actions.keys() raising forces the except path.
    bad = Mock()
    bad.keys.side_effect = RuntimeError("boom")
    config.model_actions = bad
    pipeline = make_pipeline(config_manager=config)
    assert pipeline._match_command("hello") is None


# ---------------------------------------------------------------------------
# _execute_command
# ---------------------------------------------------------------------------


def test_execute_command_no_executor():
    pipeline = make_pipeline()
    assert pipeline._execute_command("hello") is False


def test_execute_command_none_result_is_success():
    executor = Mock()
    executor.execute_command.return_value = None
    pipeline = make_pipeline(command_executor=executor)
    assert pipeline._execute_command("hello") is True


def test_execute_command_false_result_is_failure():
    executor = Mock()
    executor.execute_command.return_value = False
    pipeline = make_pipeline(command_executor=executor)
    assert pipeline._execute_command("hello") is False


def test_execute_command_exception_returns_false():
    executor = Mock()
    executor.execute_command.side_effect = RuntimeError("boom")
    pipeline = make_pipeline(command_executor=executor)
    assert pipeline._execute_command("hello") is False


# ---------------------------------------------------------------------------
# trigger_mock_wake_word
# ---------------------------------------------------------------------------


def test_trigger_mock_wake_word_present():
    pipeline = make_pipeline()
    pipeline.wake_detector = Mock()
    pipeline.trigger_mock_wake_word("hey_jarvis")
    pipeline.wake_detector.trigger_wake_word.assert_called_once_with("hey_jarvis")


def test_trigger_mock_wake_word_absent_logs_warning():
    pipeline = make_pipeline()

    # Detector without trigger_wake_word attribute.
    class NoTrigger:
        pass

    pipeline.wake_detector = NoTrigger()
    # Should not raise.
    pipeline.trigger_mock_wake_word("hey")


# ---------------------------------------------------------------------------
# process_text_command
# ---------------------------------------------------------------------------


def test_process_text_command_success_returns_name():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = True
    pipeline = make_pipeline(
        config_manager=config, command_executor=executor, voice_only=True
    )
    install_fake_io(pipeline)
    cb = Mock()
    pipeline.add_command_callback(cb)
    assert pipeline.process_text_command("say hello") == "hello"
    cb.assert_called_once_with("hello", "say hello")
    pipeline.tts.speak.assert_called_once_with("hello")


def test_process_text_command_exec_failure_speaks_and_returns_none():
    config = Mock()
    config.model_actions = {"hello": {}}
    executor = Mock()
    executor.execute_command.return_value = False
    pipeline = make_pipeline(
        config_manager=config, command_executor=executor, voice_only=True
    )
    install_fake_io(pipeline)
    assert pipeline.process_text_command("say hello") is None
    pipeline.tts.speak.assert_called_once_with("Failed to execute hello")


def test_process_text_command_no_match_speaks_apology():
    config = Mock()
    config.model_actions = {"hello": {}}
    pipeline = make_pipeline(config_manager=config, voice_only=True)
    install_fake_io(pipeline)
    assert pipeline.process_text_command("xyzzy") is None
    pipeline.tts.speak.assert_called_once_with("Sorry, I didn't understand that")


def test_process_text_command_no_match_no_voice_only_silent():
    config = Mock()
    config.model_actions = {"hello": {}}
    pipeline = make_pipeline(config_manager=config, voice_only=False)
    install_fake_io(pipeline)
    assert pipeline.process_text_command("xyzzy") is None
    pipeline.tts.speak.assert_not_called()


# ---------------------------------------------------------------------------
# status / is_listening
# ---------------------------------------------------------------------------


def test_get_status_with_mock_detector():
    pipeline = make_pipeline(wake_words=["hey_jarvis"])
    install_fake_io(pipeline)
    status = pipeline.get_status()
    assert set(status) == {
        "listening",
        "processing",
        "wake_detector_available",
        "transcriber_available",
        "transcriber_info",
        "available_wake_words",
    }
    assert status["listening"] is False
    assert status["transcriber_available"] is True


def test_get_status_detector_without_optional_methods():
    pipeline = make_pipeline()
    install_fake_io(pipeline)

    class BareDetector:
        pass

    pipeline.wake_detector = BareDetector()
    status = pipeline.get_status()
    # Falls back to True / [] when methods are missing.
    assert status["wake_detector_available"] is True
    assert status["available_wake_words"] == []


def test_is_listening_reflects_flags():
    pipeline = make_pipeline()
    assert pipeline.is_listening() is False
    pipeline._listening = True
    pipeline._processing = False
    assert pipeline.is_listening() is True
    pipeline._processing = True
    assert pipeline.is_listening() is False
