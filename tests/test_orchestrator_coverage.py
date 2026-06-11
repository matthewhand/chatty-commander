"""Coverage for src/chatty_commander/app/orchestrator.py uncovered branches.

Complements tests/test_main_orchestrator.py without duplicating it. Focuses on:
- TextInputAdapter.feed gating (started/not-started)
- DummyAdapter lifecycle
- OpenWakeWordAdapter start/stop/callback (with VOICE deps mocked at the
  orchestrator import boundary)
- select_adapters branches: gui, computer_vision, openwakeword (VOICE on/off,
  construction-error fallback), discord bridge with advisors disabled
- ModeOrchestrator.start auto-select, stop() swallowing adapter errors
- _dispatch_command, _handle_wake_word success/fallback/total-failure paths
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import chatty_commander.app.orchestrator as orch_mod
from chatty_commander.app.orchestrator import (
    DiscordBridgeAdapter,
    DummyAdapter,
    ModeOrchestrator,
    OpenWakeWordAdapter,
    OrchestratorFlags,
    TextInputAdapter,
)


class _CommandSink:
    def __init__(self, raise_on=None):
        self.executed = []
        self._raise_on = raise_on or set()

    def execute_command(self, command_name: str):
        self.executed.append(command_name)
        if command_name in self._raise_on:
            raise RuntimeError(f"no command {command_name}")
        return f"ran:{command_name}"


class _ConfigAdvisorsOff:
    advisors = {"enabled": False}


class _ConfigAdvisorsOn:
    advisors = {"enabled": True}


# ── TextInputAdapter ─────────────────────────────────────────────────────


class TestTextInputAdapter:
    def test_feed_before_start_is_noop(self):
        received = []
        adapter = TextInputAdapter(on_command=received.append)
        adapter.feed("ignored")
        assert received == []

    def test_feed_after_start_dispatches(self):
        received = []
        adapter = TextInputAdapter(on_command=received.append)
        adapter.start()
        adapter.feed("hello")
        assert received == ["hello"]

    def test_feed_after_stop_is_noop_again(self):
        received = []
        adapter = TextInputAdapter(on_command=received.append)
        adapter.start()
        adapter.stop()
        adapter.feed("nope")
        assert received == []


# ── DummyAdapter ─────────────────────────────────────────────────────────


class TestDummyAdapter:
    def test_name_and_lifecycle(self):
        adapter = DummyAdapter("gui")
        assert adapter.name == "gui"
        assert adapter._started is False
        adapter.start()
        assert adapter._started is True
        adapter.stop()
        assert adapter._started is False


# ── OpenWakeWordAdapter ──────────────────────────────────────────────────


class _FakeDetector:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.callbacks = []
        self.listening = False

    def add_callback(self, cb):
        self.callbacks.append(cb)

    def start_listening(self):
        self.listening = True

    def stop_listening(self):
        self.listening = False


class TestOpenWakeWordAdapter:
    def test_start_raises_when_voice_unavailable(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", False)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        try:
            adapter.start()
            raised = False
        except ImportError as e:
            raised = True
            assert "Voice dependencies" in str(e)
        assert raised

    def test_start_uses_real_detector_with_config(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", _FakeDetector)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        config = SimpleNamespace(
            wake_words=["computer"], wake_word_threshold=0.7
        )
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None, config=config)
        adapter.start()
        assert adapter._started is True
        assert isinstance(adapter._detector, _FakeDetector)
        assert adapter._detector.kwargs["wake_words"] == ["computer"]
        assert adapter._detector.kwargs["threshold"] == 0.7
        assert adapter._detector.listening is True

    def test_start_defaults_when_config_missing_attrs(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", _FakeDetector)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None, config=None)
        adapter.start()
        assert adapter._detector.kwargs["wake_words"] == ["hey_jarvis", "alexa"]
        assert adapter._detector.kwargs["threshold"] == 0.5

    def test_start_falls_back_to_mock_on_real_detector_error(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)

        class _Boom:
            def __init__(self, *a, **k):
                raise RuntimeError("no audio device")

        monkeypatch.setattr(orch_mod, "WakeWordDetector", _Boom)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        adapter.start()
        assert isinstance(adapter._detector, _FakeDetector)
        assert adapter._detector.listening is True

    def test_start_no_detector_when_classes_none(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", None)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", None)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        adapter.start()
        assert adapter._detector is None
        assert adapter._started is True

    def test_start_is_idempotent_when_already_started(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", _FakeDetector)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        adapter.start()
        first_detector = adapter._detector
        adapter.start()  # second call returns early
        assert adapter._detector is first_detector

    def test_stop_calls_detector_stop_listening(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", _FakeDetector)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        adapter.start()
        detector = adapter._detector
        adapter.stop()
        assert adapter._started is False
        assert detector.listening is False

    def test_stop_without_start_is_safe(self):
        adapter = OpenWakeWordAdapter(on_wake_word=lambda w, c: None)
        adapter.stop()  # _detector is None / not started
        assert adapter._started is False

    def test_handle_wake_word_invokes_callback(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        monkeypatch.setattr(orch_mod, "WakeWordDetector", _FakeDetector)
        monkeypatch.setattr(orch_mod, "MockWakeWordDetector", _FakeDetector)
        calls = []
        adapter = OpenWakeWordAdapter(
            on_wake_word=lambda w, c: calls.append((w, c))
        )
        adapter.start()
        # The registered callback is _handle_wake_word; invoke it.
        adapter._detector.callbacks[0]("hey_jarvis", 0.91)
        assert calls == [("hey_jarvis", 0.91)]


# ── select_adapters: gui / cv / openwakeword branches ────────────────────


class TestSelectAdaptersBranches:
    def _orch(self, flags, config=None, advisor_sink=None):
        return ModeOrchestrator(
            config=config or _ConfigAdvisorsOff(),
            command_sink=_CommandSink(),
            advisor_sink=advisor_sink,
            flags=flags,
        )

    def test_gui_only(self):
        orch = self._orch(OrchestratorFlags(enable_gui=True))
        assert orch.select_adapters() == ["gui"]
        assert isinstance(orch.adapters[0], DummyAdapter)

    def test_computer_vision_only(self):
        orch = self._orch(OrchestratorFlags(enable_computer_vision=True))
        assert orch.select_adapters() == ["computer_vision"]

    def test_openwakeword_dummy_when_voice_unavailable(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", False)
        orch = self._orch(OrchestratorFlags(enable_openwakeword=True))
        assert orch.select_adapters() == ["openwakeword"]
        assert isinstance(orch.adapters[0], DummyAdapter)

    def test_openwakeword_real_adapter_when_voice_available(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        orch = self._orch(OrchestratorFlags(enable_openwakeword=True))
        assert orch.select_adapters() == ["openwakeword"]
        assert isinstance(orch.adapters[0], OpenWakeWordAdapter)

    def test_openwakeword_falls_back_to_dummy_on_construction_error(
        self, monkeypatch
    ):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)

        def _boom(*a, **k):
            raise RuntimeError("ctor failure")

        monkeypatch.setattr(orch_mod, "OpenWakeWordAdapter", _boom)
        orch = self._orch(OrchestratorFlags(enable_openwakeword=True))
        assert orch.select_adapters() == ["openwakeword"]
        assert isinstance(orch.adapters[0], DummyAdapter)

    def test_discord_bridge_not_selected_when_advisors_disabled(self):
        # Flag on but config.advisors.enabled is False -> bridge skipped entirely.
        orch = self._orch(
            OrchestratorFlags(enable_discord_bridge=True),
            config=_ConfigAdvisorsOff(),
            advisor_sink=MagicMock(),
        )
        assert orch.select_adapters() == []

    def test_discord_bridge_skipped_when_config_has_no_advisors_attr(self):
        orch = ModeOrchestrator(
            config=SimpleNamespace(),  # no .advisors -> getattr default {}
            command_sink=_CommandSink(),
            advisor_sink=MagicMock(),
            flags=OrchestratorFlags(enable_discord_bridge=True),
        )
        assert orch.select_adapters() == []

    def test_all_flags_combination(self, monkeypatch):
        monkeypatch.setattr(orch_mod, "VOICE_AVAILABLE", True)
        orch = ModeOrchestrator(
            config=_ConfigAdvisorsOn(),
            command_sink=_CommandSink(),
            advisor_sink=_RecordingAdvisorSink(),
            flags=OrchestratorFlags(
                enable_text=True,
                enable_gui=True,
                enable_web=True,
                enable_openwakeword=True,
                enable_computer_vision=True,
                enable_discord_bridge=True,
            ),
        )
        names = orch.select_adapters()
        assert set(names) == {
            "text",
            "gui",
            "web",
            "openwakeword",
            "computer_vision",
            "discord_bridge",
        }


# ── start / stop lifecycle ───────────────────────────────────────────────


class _RecordingAdvisorSink:
    def __init__(self):
        self.messages = []

    def handle_message(self, message):
        self.messages.append(message)
        return "reply"


class TestStartStopLifecycle:
    def test_start_auto_selects_when_no_adapters(self):
        orch = ModeOrchestrator(
            config=_ConfigAdvisorsOff(),
            command_sink=_CommandSink(),
            flags=OrchestratorFlags(enable_text=True),
        )
        # select_adapters not called yet
        assert orch.adapters == []
        names = orch.start()
        assert names == ["text"]
        assert orch.adapters[0]._started is True

    def test_start_does_not_reselect_when_adapters_present(self):
        orch = ModeOrchestrator(
            config=_ConfigAdvisorsOff(),
            command_sink=_CommandSink(),
            flags=OrchestratorFlags(enable_text=True),
        )
        orch.select_adapters()
        existing = orch.adapters[0]
        orch.start()
        assert orch.adapters[0] is existing

    def test_stop_swallows_adapter_exceptions(self):
        orch = ModeOrchestrator(
            config=_ConfigAdvisorsOff(),
            command_sink=_CommandSink(),
            flags=OrchestratorFlags(),
        )

        class _Boom:
            name = "boom"

            def start(self):
                pass

            def stop(self):
                raise RuntimeError("stop failed")

        good = DummyAdapter("good")
        good.start()
        orch.adapters = [_Boom(), good]
        # Should not raise despite first adapter throwing.
        orch.stop()
        assert good._started is False


# ── routing: _dispatch_command and _handle_wake_word ─────────────────────


class TestDispatchAndWakeWord:
    def _orch(self, command_sink):
        return ModeOrchestrator(
            config=_ConfigAdvisorsOff(),
            command_sink=command_sink,
            flags=OrchestratorFlags(),
        )

    def test_dispatch_command_forwards_to_sink(self):
        sink = _CommandSink()
        orch = self._orch(sink)
        assert orch._dispatch_command("ping") == "ran:ping"
        assert sink.executed == ["ping"]

    def test_handle_wake_word_dispatches_specific_command(self):
        sink = _CommandSink()
        orch = self._orch(sink)
        orch._handle_wake_word("jarvis", 0.8)
        assert sink.executed == ["wake_word_jarvis"]

    def test_handle_wake_word_falls_back_to_generic_wake(self):
        # Specific command raises -> falls back to "wake".
        sink = _CommandSink(raise_on={"wake_word_jarvis"})
        orch = self._orch(sink)
        orch._handle_wake_word("jarvis", 0.8)
        assert sink.executed == ["wake_word_jarvis", "wake"]

    def test_handle_wake_word_logs_when_both_fail(self, caplog):
        sink = _CommandSink(raise_on={"wake_word_jarvis", "wake"})
        orch = self._orch(sink)
        with caplog.at_level(
            "WARNING", logger="chatty_commander.app.orchestrator"
        ):
            orch._handle_wake_word("jarvis", 0.42)
        assert sink.executed == ["wake_word_jarvis", "wake"]
        assert any(
            "Failed to dispatch wake word" in r.getMessage()
            for r in caplog.records
        )


# ── DiscordBridgeAdapter direct unit coverage ────────────────────────────


class TestDiscordBridgeAdapter:
    def test_feed_before_start_returns_none(self):
        adapter = DiscordBridgeAdapter(on_message=lambda m: "handled")
        assert adapter.feed("msg") is None

    def test_feed_after_start_returns_handler_result(self):
        adapter = DiscordBridgeAdapter(on_message=lambda m: f"handled:{m}")
        adapter.start()
        assert adapter.feed("msg") == "handled:msg"

    def test_feed_after_stop_returns_none(self):
        adapter = DiscordBridgeAdapter(on_message=lambda m: "handled")
        adapter.start()
        adapter.stop()
        assert adapter.feed("msg") is None
