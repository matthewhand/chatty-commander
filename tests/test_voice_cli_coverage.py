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

"""Coverage tests for chatty_commander.voice.cli.

All audio/hardware/model boundaries are patched so no devices or models are
touched. We drive the CLI handlers directly through their argparse Namespace
contract and via the assembled argparse parser to exercise arg parsing.
"""

from __future__ import annotations

import argparse
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.voice import cli as voice_cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_status():
    return {
        "transcriber_info": {
            "backend_type": "mock",
            "sample_rate": 16000,
            "channels": 1,
        },
        "transcriber_available": True,
        "available_wake_words": ["hey_jarvis"],
    }


def _make_pipeline_mock():
    pipeline = MagicMock()
    pipeline.get_status.return_value = _mock_status()
    return pipeline


# ---------------------------------------------------------------------------
# add_voice_subcommands / argparse wiring
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cc")
    subparsers = parser.add_subparsers(dest="command")
    voice_cli.add_voice_subcommands(subparsers)
    return parser


def test_add_voice_subcommands_test_defaults():
    parser = _build_parser()
    args = parser.parse_args(["voice", "test"])
    assert args.voice_command == "test"
    assert args.mock is False
    assert args.duration == 30
    assert args.wake_words is None
    # The voice parser sets a dispatch func.
    assert callable(args.func)


def test_add_voice_subcommands_test_with_flags():
    parser = _build_parser()
    args = parser.parse_args(
        ["voice", "test", "--mock", "--duration", "5", "--wake-words", "a", "b"]
    )
    assert args.mock is True
    assert args.duration == 5
    assert args.wake_words == ["a", "b"]


def test_add_voice_subcommands_transcribe_defaults_and_choices():
    parser = _build_parser()
    args = parser.parse_args(["voice", "transcribe"])
    assert args.backend == "whisper_local"
    assert args.timeout == 5.0

    args = parser.parse_args(
        ["voice", "transcribe", "--backend", "mock", "--timeout", "2.5"]
    )
    assert args.backend == "mock"
    assert args.timeout == 2.5


def test_add_voice_subcommands_transcribe_invalid_backend_exits():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["voice", "transcribe", "--backend", "bogus"])


def test_add_voice_subcommands_selftest_run_and_improve():
    parser = _build_parser()
    args = parser.parse_args(
        ["voice", "self-test", "run", "--openai-key", "k", "--phrases", "one", "two"]
    )
    assert args.voice_command == "self-test"
    assert args.test_command == "run"
    assert args.openai_key == "k"
    assert args.phrases == ["one", "two"]

    args = parser.parse_args(
        ["voice", "self-test", "improve", "--iterations", "7", "--openai-key", "k2"]
    )
    assert args.test_command == "improve"
    assert args.iterations == 7


def test_add_voice_subcommands_func_dispatch(monkeypatch):
    parser = _build_parser()
    args = parser.parse_args(["voice", "status"])
    called = {}
    monkeypatch.setattr(
        voice_cli, "handle_voice_command", lambda a: called.setdefault("ran", a)
    )
    # func was bound to a lambda calling handle_voice_command at definition time;
    # patching the module attribute means we invoke the real lambda which will
    # look up the (now patched) name.
    args.func(args)
    assert called["ran"] is args


# ---------------------------------------------------------------------------
# handle_voice_command dispatch
# ---------------------------------------------------------------------------


def test_handle_voice_command_no_attr(capsys):
    voice_cli.handle_voice_command(SimpleNamespace())
    out = capsys.readouterr().out
    assert "No voice command specified" in out


def test_handle_voice_command_empty(capsys):
    voice_cli.handle_voice_command(SimpleNamespace(voice_command=None))
    out = capsys.readouterr().out
    assert "No voice command specified" in out


def test_handle_voice_command_unknown(capsys):
    voice_cli.handle_voice_command(SimpleNamespace(voice_command="frobnicate"))
    out = capsys.readouterr().out
    assert "Unknown voice command: frobnicate" in out


def test_handle_voice_command_dispatch_test():
    args = SimpleNamespace(voice_command="test")
    with patch.object(voice_cli, "_handle_voice_test") as h:
        voice_cli.handle_voice_command(args, "cfg", "exec", "state")
    h.assert_called_once_with(args, "cfg", "exec", "state")


def test_handle_voice_command_dispatch_status():
    args = SimpleNamespace(voice_command="status")
    with patch.object(voice_cli, "_handle_voice_status") as h:
        voice_cli.handle_voice_command(args)
    h.assert_called_once_with(args)


def test_handle_voice_command_dispatch_transcribe():
    args = SimpleNamespace(voice_command="transcribe")
    with patch.object(voice_cli, "_handle_voice_transcribe") as h:
        voice_cli.handle_voice_command(args)
    h.assert_called_once_with(args)


def test_handle_voice_command_dispatch_self_test_ok():
    args = SimpleNamespace(voice_command="self-test")
    fake_mod = types.ModuleType("chatty_commander.voice.self_test")
    fake_mod.handle_self_test_command = MagicMock()
    with patch.dict(
        sys.modules, {"chatty_commander.voice.self_test": fake_mod}
    ):
        voice_cli.handle_voice_command(args)
    fake_mod.handle_self_test_command.assert_called_once_with(args)


def test_handle_voice_command_dispatch_self_test_import_error(capsys):
    args = SimpleNamespace(voice_command="self-test")
    real_import = __import__

    def fake_import(name, *a, **k):
        if name == "chatty_commander.voice.self_test" or name.endswith("self_test"):
            raise ImportError("no module")
        return real_import(name, *a, **k)

    with patch("builtins.__import__", side_effect=fake_import):
        voice_cli.handle_voice_command(args)
    out = capsys.readouterr().out
    assert "Self-test not available" in out


# ---------------------------------------------------------------------------
# _handle_voice_test
# ---------------------------------------------------------------------------


def test_handle_voice_test_mock_path(capsys):
    pipeline = _make_pipeline_mock()
    args = SimpleNamespace(wake_words=None, mock=True, duration=0)
    with (
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline) as P,
        patch.object(voice_cli.time, "sleep") as sleep,
    ):
        voice_cli._handle_voice_test(args)

    out = capsys.readouterr().out
    assert "Starting voice pipeline test" in out
    assert "Pipeline status" in out
    assert "Mock mode" in out
    assert "Testing mock wake word" in out
    assert "test completed" in out

    P.assert_called_once()
    pipeline.add_command_callback.assert_called_once()
    pipeline.start.assert_called_once()
    pipeline.trigger_mock_wake_word.assert_called_once_with("hey_jarvis")
    pipeline.process_text_command.assert_called_once_with("hello there")
    pipeline.stop.assert_called_once()
    # mock path sleeps 2 + 2 + duration(0) = 3 calls
    assert sleep.call_count == 3


def test_handle_voice_test_callback_branches(capsys):
    pipeline = _make_pipeline_mock()
    captured = {}

    def grab(cb):
        captured["cb"] = cb

    pipeline.add_command_callback.side_effect = grab
    args = SimpleNamespace(wake_words=["x"], mock=True, duration=0)
    with (
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
        patch.object(voice_cli.time, "sleep"),
    ):
        voice_cli._handle_voice_test(args)

    cb = captured["cb"]
    cb("turn_on", "turn on lights")
    cb("", "garbled audio")
    out = capsys.readouterr().out
    assert "Command executed: 'turn_on'" in out
    assert "No command matched: 'garbled audio'" in out


def test_handle_voice_test_real_path(capsys):
    pipeline = _make_pipeline_mock()
    args = SimpleNamespace(wake_words=None, mock=False, duration=0)
    with (
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
        patch.object(voice_cli.time, "sleep") as sleep,
    ):
        voice_cli._handle_voice_test(args)

    out = capsys.readouterr().out
    assert "Say a wake word" in out
    assert "Mock mode" not in out
    pipeline.trigger_mock_wake_word.assert_not_called()
    # real path only sleeps for duration -> 1 call
    assert sleep.call_count == 1


def test_handle_voice_test_exception(capsys):
    args = SimpleNamespace(wake_words=None, mock=False, duration=0)
    with patch.object(
        voice_cli, "VoicePipeline", side_effect=RuntimeError("boom")
    ):
        voice_cli._handle_voice_test(args)
    out = capsys.readouterr().out
    assert "Voice test failed: boom" in out


# ---------------------------------------------------------------------------
# _handle_voice_status
# ---------------------------------------------------------------------------


def test_handle_voice_status_deps_available(capsys):
    pipeline = _make_pipeline_mock()
    with (
        patch("importlib.util.find_spec", return_value=object()),
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
    ):
        voice_cli._handle_voice_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Voice System Status" in out
    assert "OpenWakeWord: Available" in out
    assert "Pipeline Status" in out
    assert "Sample rate: 16000 Hz" in out
    assert "Channels: 1" in out


def test_handle_voice_status_deps_missing(capsys):
    pipeline = _make_pipeline_mock()
    with (
        patch("importlib.util.find_spec", return_value=None),
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
    ):
        voice_cli._handle_voice_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Not installed" in out


def test_handle_voice_status_pipeline_failure(capsys):
    with (
        patch("importlib.util.find_spec", return_value=None),
        patch.object(
            voice_cli, "VoicePipeline", side_effect=RuntimeError("nopipe")
        ),
    ):
        voice_cli._handle_voice_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Pipeline test failed: nopipe" in out


def test_handle_voice_status_outer_failure(capsys):
    # Force the outer try to blow up by making importlib import fail.
    with patch.dict(sys.modules, {"importlib.util": None}):
        # importing importlib.util with a None entry raises ImportError
        voice_cli._handle_voice_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Status check failed" in out


# ---------------------------------------------------------------------------
# _handle_voice_transcribe
# ---------------------------------------------------------------------------


def _patch_transcriber(transcriber):
    fake_mod = types.ModuleType("chatty_commander.voice.transcription")
    fake_mod.VoiceTranscriber = MagicMock(return_value=transcriber)
    return patch.dict(
        sys.modules, {"chatty_commander.voice.transcription": fake_mod}
    ), fake_mod


def test_handle_voice_transcribe_mock_backend(capsys):
    transcriber = MagicMock()
    transcriber.is_available.return_value = True
    transcriber.get_backend_info.return_value = {"backend": "mock"}
    transcriber.transcribe_audio_data.return_value = "mock text"
    ctx, fake_mod = _patch_transcriber(transcriber)
    args = SimpleNamespace(backend="mock", timeout=1.0)
    with ctx:
        voice_cli._handle_voice_transcribe(args)
    out = capsys.readouterr().out
    assert "Testing transcription with mock backend" in out
    assert "Mock transcription: 'mock text'" in out
    transcriber.transcribe_audio_data.assert_called_once_with(b"dummy_audio")


def test_handle_voice_transcribe_not_available(capsys):
    transcriber = MagicMock()
    transcriber.is_available.return_value = False
    ctx, _ = _patch_transcriber(transcriber)
    args = SimpleNamespace(backend="whisper_local", timeout=1.0)
    with ctx:
        voice_cli._handle_voice_transcribe(args)
    out = capsys.readouterr().out
    assert "not available" in out


def test_handle_voice_transcribe_real_with_result(capsys):
    transcriber = MagicMock()
    transcriber.is_available.return_value = True
    transcriber.get_backend_info.return_value = {"backend": "whisper_local"}
    transcriber.record_and_transcribe.return_value = "hello world"
    ctx, _ = _patch_transcriber(transcriber)
    args = SimpleNamespace(backend="whisper_local", timeout=3.0)
    with ctx:
        voice_cli._handle_voice_transcribe(args)
    out = capsys.readouterr().out
    assert "Recording for 3.0 seconds" in out
    assert "Transcription: 'hello world'" in out


def test_handle_voice_transcribe_real_no_result(capsys):
    transcriber = MagicMock()
    transcriber.is_available.return_value = True
    transcriber.get_backend_info.return_value = {}
    transcriber.record_and_transcribe.return_value = None
    ctx, _ = _patch_transcriber(transcriber)
    args = SimpleNamespace(backend="whisper_api", timeout=1.0)
    with ctx:
        voice_cli._handle_voice_transcribe(args)
    out = capsys.readouterr().out
    assert "No transcription received" in out


def test_handle_voice_transcribe_exception(capsys):
    fake_mod = types.ModuleType("chatty_commander.voice.transcription")
    fake_mod.VoiceTranscriber = MagicMock(side_effect=RuntimeError("kaboom"))
    args = SimpleNamespace(backend="mock", timeout=1.0)
    with patch.dict(
        sys.modules, {"chatty_commander.voice.transcription": fake_mod}
    ):
        voice_cli._handle_voice_transcribe(args)
    out = capsys.readouterr().out
    assert "Transcription test failed: kaboom" in out


# ---------------------------------------------------------------------------
# demo_voice_integration
# ---------------------------------------------------------------------------


def test_demo_voice_integration_happy(capsys):
    pipeline = _make_pipeline_mock()
    captured = {}
    pipeline.add_command_callback.side_effect = lambda cb: captured.setdefault(
        "cb", cb
    )
    config_manager = SimpleNamespace(model_actions={"hello": {}, "lights": {}})
    with (
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
        patch.object(voice_cli.time, "sleep"),
    ):
        voice_cli.demo_voice_integration(config_manager=config_manager)

    # exercise the demo callback both branches
    captured["cb"]("hello", "hello world")
    captured["cb"]("", "junk")
    out = capsys.readouterr().out
    assert "Voice Integration Demo" in out
    assert "Available commands" in out
    assert "- hello" in out
    assert "Executed: hello" in out
    assert "Unknown: 'junk'" in out
    assert "Demo completed" in out
    assert pipeline.process_text_command.call_count == 4


def test_demo_voice_integration_no_config(capsys):
    pipeline = _make_pipeline_mock()
    with (
        patch.object(voice_cli, "VoicePipeline", return_value=pipeline),
        patch.object(voice_cli.time, "sleep"),
    ):
        voice_cli.demo_voice_integration()
    out = capsys.readouterr().out
    assert "Available commands" not in out
    assert "Demo completed" in out


def test_demo_voice_integration_exception(capsys):
    with patch.object(
        voice_cli, "VoicePipeline", side_effect=RuntimeError("demoboom")
    ):
        voice_cli.demo_voice_integration()
    out = capsys.readouterr().out
    assert "Demo failed: demoboom" in out
