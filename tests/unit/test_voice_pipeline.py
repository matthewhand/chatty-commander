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

"""Dedicated unit tests for VoicePipeline (addressing 'no tests found' gap)."""

from unittest.mock import Mock, patch

from chatty_commander.voice.pipeline import VoicePipeline
from chatty_commander.voice.wakeword import MockWakeWordDetector


class TestVoicePipelineUnit:
    """Focused unit tests for core VoicePipeline behavior."""

    def setup_method(self):
        self.mock_config = Mock()
        self.mock_config.model_actions = {
            "hello": {"action": "custom_message", "message": "hi"},
            "lights": {"action": "url", "url": "http://ex.com"},
        }
        self.mock_executor = Mock()
        self.mock_executor.execute_command.return_value = True
        self.mock_state = Mock()

    def test_init_with_mocks(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=self.mock_state,
            use_mock=True,
        )
        assert isinstance(pipeline.wake_detector, MockWakeWordDetector)
        assert not pipeline.is_listening()
        assert pipeline.get_status()["listening"] is False

    def test_start_stop_lifecycle(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.start()
        assert pipeline.is_listening()

        pipeline.stop()
        assert not pipeline.is_listening()

    def test_process_text_command_success(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        result = pipeline.process_text_command("hello there")
        assert result == "hello"
        self.mock_executor.execute_command.assert_called_with("hello")

    def test_process_text_command_no_match(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        result = pipeline.process_text_command("unknown foo bar")
        assert result is None
        # unmatched still notifies (empty name)
        # callbacks tested separately

    def test_callbacks_registration_and_fire(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        calls = []

        def cb(name, text):
            calls.append((name, text))

        pipeline.add_command_callback(cb)
        pipeline.process_text_command("hello")
        assert len(calls) == 1
        assert calls[0][0] == "hello"

        pipeline.remove_command_callback(cb)
        pipeline.process_text_command("hello")
        assert len(calls) == 1  # no additional

    def test_mock_wake_trigger(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        # should not raise
        pipeline.trigger_mock_wake_word("hey_jarvis")

    def test_error_in_transcribe_is_caught(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        # patch transcriber to raise
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.side_effect = RuntimeError("boom")
        # should not propagate, just log
        pipeline._process_voice_command("wake")
        # processing flag reset in finally
        assert not pipeline._processing

    def test_execute_command_no_executor(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=None,
            use_mock=True,
        )
        ok = pipeline._execute_command("hello")
        assert ok is False

    def test_get_status_and_is_listening(self):
        """Test get_status and is_listening report state correctly."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=self.mock_state,
            use_mock=True,
        )
        status = pipeline.get_status()
        assert "listening" in status
        assert "processing" in status
        assert "transcriber_available" in status
        assert not pipeline.is_listening()

    def test_on_wake_word_starts_background_process(self):
        """_on_wake_word_detected should spawn daemon thread for _process (no crash)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        with patch("threading.Thread") as mock_t:
            mock_t.return_value.start = Mock()
            pipeline._on_wake_word_detected("hey_chat_tee", 0.95)
            mock_t.assert_called_once()
            args, kwargs = mock_t.call_args
            assert kwargs.get("target") == pipeline._process_voice_command or args[1][0] == pipeline._process_voice_command
            mock_t.return_value.start.assert_called_once()

    def test_process_voice_command_success_path(self):
        """Full _process success: transcribe -> match direct/keyword -> execute -> notify."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "hello"
        calls = []
        pipeline.add_command_callback(lambda n, t: calls.append((n, t)))
        pipeline._process_voice_command("wake")
        self.mock_executor.execute_command.assert_called_with("hello")
        assert len(calls) == 1
        assert not pipeline._processing

    def test_process_voice_command_no_transcription(self):
        """_process early return on empty transcription, no side effects."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = ""
        pipeline._process_voice_command("wake")
        self.mock_executor.execute_command.assert_not_called()
        assert not pipeline._processing

    def test_process_voice_command_keyword_match(self):
        """Transcription matches via keyword helper."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "turn on lights"
        pipeline._process_voice_command("wake")
        self.mock_executor.execute_command.assert_called_with("lights")

    def test_voice_only_speaks_command_on_success(self):
        """voice_only=True triggers tts.speak(command_name) on matched success."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.voice_only = True
        pipeline.tts = Mock()
        pipeline.tts.is_available.return_value = True
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "hello"
        pipeline._process_voice_command("wake")
        pipeline.tts.speak.assert_called_with("hello")

    def test_voice_only_speaks_failure_on_execute_fail(self):
        """voice_only=True speaks failure message when execute returns False."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        self.mock_executor.execute_command.return_value = False
        pipeline.voice_only = True
        pipeline.tts = Mock()
        pipeline.tts.is_available.return_value = True
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "hello"
        pipeline._process_voice_command("wake")
        pipeline.tts.speak.assert_called_with("Failed to execute hello")

    def test_unmatched_transcription_voice_only_speaks_apology(self):
        """Unmatched transcription with voice_only speaks a fixed apology."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.voice_only = True
        pipeline.tts = Mock()
        pipeline.tts.is_available.return_value = True
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "unknown words here"
        pipeline._process_voice_command("wake")
        pipeline.tts.speak.assert_called_with("Sorry, I didn't understand that")

    def test_process_text_command_voice_only(self):
        """process_text_command respects voice_only for tts feedback."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.voice_only = True
        pipeline.tts = Mock()
        pipeline.tts.is_available.return_value = True
        result = pipeline.process_text_command("lights on")
        assert result == "lights"
        pipeline.tts.speak.assert_called_with("lights")

    def test_start_already_listening_is_noop(self):
        """start() when already listening warns and returns without re-start."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        pipeline.start()
        assert pipeline.is_listening()
        # second start should be noop (no exception)
        pipeline.start()
        assert pipeline.is_listening()

    def test_match_command_no_config_manager(self):
        """_match_command returns None gracefully when no config_manager."""
        pipeline = VoicePipeline(
            config_manager=None,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        result = pipeline._match_command("hello")
        assert result is None

    def test_notify_callbacks_swallows_errors(self):
        """_notify_callbacks continues and swallows per-callback exceptions."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        bad_calls = []
        good_calls = []

        def bad_cb(name, text):
            bad_calls.append(1)
            raise RuntimeError("cb boom")

        def good_cb(name, text):
            good_calls.append((name, text))

        pipeline.add_command_callback(bad_cb)
        pipeline.add_command_callback(good_cb)
        # should not raise, good one still called
        pipeline._notify_callbacks("hello", "hi")
        assert len(bad_calls) == 1
        assert len(good_calls) == 1

    def test_state_manager_changes_during_process(self):
        """_process_voice_command calls state changes via safe helper when state_manager present."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=self.mock_state,
            use_mock=True,
        )
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "hello"
        pipeline._process_voice_command("wake")
        # voice_recording and voice_listening (final) should have been attempted
        assert self.mock_state.change_state.call_count >= 1

    def test_match_command_handles_exception(self):
        """_match_command returns None and swallows exceptions (error path coverage)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        bad = Mock()
        bad.model_actions = Mock(side_effect=RuntimeError("boom"))
        pipeline.config_manager = bad
        result = pipeline._match_command("hello")
        assert result is None

    def test_get_status_reports_fields(self):
        """get_status includes listening/processing/wake keys (covers status helper)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        status = pipeline.get_status()
        assert "listening" in status
        assert "processing" in status
        assert "wake_detector_available" in status

    def test_remove_command_callback(self):
        """Callbacks can be removed and are not fired after removal."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        calls = []

        def cb(name, text):
            calls.append((name, text))

        pipeline.add_command_callback(cb)
        pipeline.remove_command_callback(cb)
        pipeline._notify_callbacks("x", "y")
        assert calls == []

    def test_get_keyword_map_structure(self):
        """_get_keyword_map returns the expected pure mapping (extracted helper coverage)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        km = pipeline._get_keyword_map()
        assert isinstance(km, dict)
        assert "hello" in km and isinstance(km["hello"], list)
        assert "lights" in km

    def test_find_direct_name_match_behavior(self):
        """_find_direct_name_match works for substring and returns first match or None (pure helper)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        actions = {"hello": {}, "lights": {}}
        assert pipeline._find_direct_name_match("say hello now", actions) == "hello"
        assert pipeline._find_direct_name_match("turn the lights", actions) == "lights"
        assert pipeline._find_direct_name_match("unknown phrase", actions) is None

    def test_stop_is_idempotent(self):
        """stop() when not listening (or repeatedly) is safe noop and keeps consistent state."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        # not started
        pipeline.stop()
        assert not pipeline.is_listening()
        pipeline.stop()
        assert not pipeline.is_listening()

    def test_process_text_command_execute_failure_returns_none(self):
        """process_text_command returns None (not the name) when executor reports failure."""
        self.mock_executor.execute_command.return_value = False
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        result = pipeline.process_text_command("hello")
        assert result is None

    def test_is_listening_false_while_processing(self):
        """is_listening() == False while internal _processing flag is set (even if listening)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        pipeline._listening = True
        pipeline._processing = True
        assert not pipeline.is_listening()
        pipeline._processing = False
        assert pipeline.is_listening()

    def test_start_stop_call_detector_lifecycle(self):
        """start/stop forward to wake_detector start_listening / stop_listening when present."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        # ensure methods exist on the mock detector for this test
        pipeline.wake_detector.start_listening = Mock()
        pipeline.wake_detector.stop_listening = Mock()
        pipeline.start()
        pipeline.wake_detector.start_listening.assert_called_once()
        assert pipeline.is_listening()
        pipeline.stop()
        pipeline.wake_detector.stop_listening.assert_called_once()
        assert not pipeline.is_listening()

    def test_get_status_delegates_subcomponent_queries(self):
        """get_status calls optional methods on wake_detector and transcriber when available."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        pipeline.wake_detector.is_listening = Mock(return_value=False)
        pipeline.wake_detector.get_available_models = Mock(return_value=["hey_chat_tee"])
        pipeline.transcriber.is_available = Mock(return_value=True)
        pipeline.transcriber.get_backend_info = Mock(return_value={"backend": "mock"})
        status = pipeline.get_status()
        assert status["wake_detector_available"] is False
        assert status["available_wake_words"] == ["hey_chat_tee"]
        assert status["transcriber_available"] is True
        assert "transcriber_info" in status

    def test_find_direct_name_match(self):
        """_find_direct_name_match helper returns first name substring match."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        match = pipeline._find_direct_name_match(
            "say hello now", self.mock_config.model_actions
        )
        assert match == "hello"

    def test_match_by_keywords_helper(self):
        """_match_by_keywords uses _get_keyword_map for fuzzy hits (using present command)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            use_mock=True,
        )
        match = pipeline._match_by_keywords(
            "turn the lights on now", self.mock_config.model_actions
        )
        assert match == "lights"

    def test_notify_callbacks_swallows_per_callback_errors(self):
        """_notify_callbacks catches and swallows exceptions from callbacks (no crash)."""
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
        )
        seen = []
        def bad(name, text):
            seen.append("bad")
            raise ValueError("callback error")
        def good(name, text):
            seen.append("good")
        pipeline.add_command_callback(bad)
        pipeline.add_command_callback(good)
        # must not raise; both attempted
        pipeline._notify_callbacks("hello", "hi there")
        assert "bad" in seen and "good" in seen

    def test_process_voice_command_triggers_state_changes(self):
        """_process_voice_command calls state transitions via _safe_change_state when state_manager present."""
        mock_state = Mock()
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=mock_state,
            use_mock=True,
        )
        pipeline.transcriber = Mock()
        pipeline.transcriber.record_and_transcribe.return_value = "hello"
        pipeline._process_voice_command("wake")
        # recording + final listening (via safe)
        called_states = [c.args[0] for c in mock_state.change_state.call_args_list]
        assert "voice_recording" in called_states
        assert "voice_listening" in called_states
