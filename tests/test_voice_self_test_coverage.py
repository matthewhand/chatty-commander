# MIT License
#
# Copyright (c) 2024 mhand
#
# Tests for src/chatty_commander/voice/self_test.py
#
# These tests mock the VoiceTranscriber import boundary and the optional
# pyttsx3 / openai dependencies so nothing real (whisper, audio HW, network,
# LLM) is loaded. They exercise argument handling, each check/step of the
# self-test harness, success + failure/exception reporting, and output.

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import chatty_commander.voice.self_test as st
from chatty_commander.voice.self_test import (
    VoiceSelfTester,
    add_self_test_commands,
    create_self_improvement_loop,
    handle_self_test_command,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_transcriber():
    """A transcriber whose transcribe_audio_data echoes a canned string."""
    t = MagicMock()
    t.transcribe_audio_data.return_value = "hello world"
    return t


def make_tester(transcriber, **kwargs):
    """Construct a VoiceSelfTester without touching real TTS/transcriber init."""
    # Pass an explicit transcriber so VoiceTranscriber() is never constructed.
    return VoiceSelfTester(transcriber=transcriber, **kwargs)


# ---------------------------------------------------------------------------
# __init__ / TTS initialization
# ---------------------------------------------------------------------------


def test_init_uses_provided_transcriber_and_default_phrases(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester.transcriber is fake_transcriber
    assert tester.openai_client is None
    # default phrases populated
    assert len(tester.test_phrases) > 0
    assert "hello world" in tester.test_phrases
    assert tester._tts_engine is None  # TTS unavailable -> not initialized


def test_init_custom_phrases_override_defaults(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber, test_phrases=["only this"])
    assert tester.test_phrases == ["only this"]


def test_init_constructs_default_transcriber_when_none():
    # When no transcriber is passed, VoiceTranscriber(...) is invoked.
    fake = MagicMock()
    with patch.object(st, "VoiceTranscriber", return_value=fake) as ctor, patch.object(
        st, "TTS_AVAILABLE", False
    ):
        tester = VoiceSelfTester()
    ctor.assert_called_once_with(backend="whisper_local")
    assert tester.transcriber is fake


def test_init_builds_openai_client_when_available_and_key(fake_transcriber):
    fake_client = MagicMock()
    with patch.object(st, "TTS_AVAILABLE", False), patch.object(
        st, "OPENAI_AVAILABLE", True
    ), patch.object(st, "OpenAI", return_value=fake_client) as ctor:
        tester = make_tester(fake_transcriber, openai_api_key="sk-test")
    ctor.assert_called_once_with(api_key="sk-test")
    assert tester.openai_client is fake_client


def test_init_no_openai_client_when_key_missing(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False), patch.object(
        st, "OPENAI_AVAILABLE", True
    ):
        tester = make_tester(fake_transcriber, openai_api_key=None)
    assert tester.openai_client is None


def test_initialize_tts_success_selects_female_voice(fake_transcriber):
    female_voice = SimpleNamespace(name="Samantha", id="voice-samantha")
    male_voice = SimpleNamespace(name="Fred", id="voice-fred")
    engine = MagicMock()
    engine.getProperty.return_value = [male_voice, female_voice]
    fake_pyttsx3 = MagicMock()
    fake_pyttsx3.init.return_value = engine

    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "pyttsx3", fake_pyttsx3
    ):
        tester = make_tester(fake_transcriber)

    assert tester._tts_engine is engine
    engine.setProperty.assert_any_call("rate", 150)
    engine.setProperty.assert_any_call("volume", 0.9)
    # female/samantha voice chosen
    engine.setProperty.assert_any_call("voice", "voice-samantha")


def test_initialize_tts_no_voices(fake_transcriber):
    engine = MagicMock()
    engine.getProperty.return_value = []  # falsy -> skip voice selection
    fake_pyttsx3 = MagicMock()
    fake_pyttsx3.init.return_value = engine
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "pyttsx3", fake_pyttsx3
    ):
        tester = make_tester(fake_transcriber)
    assert tester._tts_engine is engine


def test_initialize_tts_exception_sets_engine_none(fake_transcriber):
    fake_pyttsx3 = MagicMock()
    fake_pyttsx3.init.side_effect = RuntimeError("no audio device")
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "pyttsx3", fake_pyttsx3
    ):
        tester = make_tester(fake_transcriber)
    assert tester._tts_engine is None


# ---------------------------------------------------------------------------
# generate_audio_from_text
# ---------------------------------------------------------------------------


def test_generate_audio_returns_none_when_no_engine(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester.generate_audio_from_text("hi") is None


def test_generate_audio_success_reads_and_unlinks(fake_transcriber, tmp_path):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    engine = MagicMock()
    tester._tts_engine = engine

    audio_bytes = b"RIFFfakeaudio"

    # Make save_to_file actually write the bytes the function later reads.
    def _save(text, name):
        with open(name, "wb") as f:
            f.write(audio_bytes)

    engine.save_to_file.side_effect = _save

    unlinked = []
    real_unlink = st.os.unlink

    def _track_unlink(p):
        unlinked.append(p)
        real_unlink(p)

    with patch.object(st.os, "unlink", side_effect=_track_unlink):
        result = tester.generate_audio_from_text("hello")

    assert result == audio_bytes
    engine.runAndWait.assert_called_once()
    assert len(unlinked) == 1  # temp file cleaned up


def test_generate_audio_exception_returns_none_and_cleans_up(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    engine = MagicMock()
    engine.save_to_file.side_effect = RuntimeError("tts boom")
    tester._tts_engine = engine

    with patch.object(st.os, "unlink") as unlink:
        result = tester.generate_audio_from_text("hello")
    assert result is None
    # finally block still attempts unlink of the created temp path
    assert unlink.called


def test_generate_audio_unlink_oserror_swallowed(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    engine = MagicMock()
    engine.save_to_file.side_effect = RuntimeError("boom")
    tester._tts_engine = engine
    with patch.object(st.os, "unlink", side_effect=OSError("gone")):
        # Should not raise despite unlink failure.
        assert tester.generate_audio_from_text("x") is None


# ---------------------------------------------------------------------------
# test_transcription_accuracy
# ---------------------------------------------------------------------------


def test_transcription_accuracy_no_audio_returns_empty(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    # No TTS engine -> generate_audio_from_text returns None
    text, acc = tester.test_transcription_accuracy("hello world")
    assert text == ""
    assert acc == 0.0
    fake_transcriber.transcribe_audio_data.assert_not_called()


def test_transcription_accuracy_with_audio(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    with patch.object(tester, "generate_audio_from_text", return_value=b"aud"):
        text, acc = tester.test_transcription_accuracy("hello world")
    assert text == "hello world"
    assert acc == 1.0  # perfect overlap
    fake_transcriber.transcribe_audio_data.assert_called_once_with(b"aud")


# ---------------------------------------------------------------------------
# _calculate_accuracy
# ---------------------------------------------------------------------------


def test_calculate_accuracy_perfect(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester._calculate_accuracy("hello world", "hello world") == 1.0


def test_calculate_accuracy_partial(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    # original={a,b}, transcribed={a,c}; intersection=1, union=3
    score = tester._calculate_accuracy("a b", "a c")
    # Plain float tolerance (not pytest.approx) so the assertion is immune to
    # sibling tests that leave a MagicMock 'numpy' in sys.modules — approx's
    # numpy detection (isinstance(val, np.bool_)) raises under that pollution.
    assert abs(score - 1 / 3) < 1e-9


def test_calculate_accuracy_empty_original_empty_transcribed(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester._calculate_accuracy("", "") == 1.0


def test_calculate_accuracy_empty_original_nonempty_transcribed(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester._calculate_accuracy("", "junk") == 0.0


# ---------------------------------------------------------------------------
# llm_judge_transcription
# ---------------------------------------------------------------------------


def test_llm_judge_no_client_falls_back_to_basic(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    result = tester.llm_judge_transcription("hello world", "hello world")
    assert result["score"] == 1.0
    assert result["feedback"] == "LLM judge not available"
    assert result["suggestions"] == []


def test_llm_judge_success_parses_json(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    payload = {"score": 0.9, "feedback": "good", "suggestions": ["x"]}
    msg = SimpleNamespace(content=json.dumps(payload))
    choice = SimpleNamespace(message=msg)
    response = SimpleNamespace(choices=[choice])
    client = MagicMock()
    client.chat.completions.create.return_value = response
    tester.openai_client = client

    result = tester.llm_judge_transcription("orig", "trans")
    assert result == payload
    client.chat.completions.create.assert_called_once()


def test_llm_judge_none_content_yields_empty_dict(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    msg = SimpleNamespace(content=None)
    response = SimpleNamespace(choices=[SimpleNamespace(message=msg)])
    client = MagicMock()
    client.chat.completions.create.return_value = response
    tester.openai_client = client
    assert tester.llm_judge_transcription("a", "a") == {}


def test_llm_judge_exception_falls_back(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("api down")
    tester.openai_client = client
    result = tester.llm_judge_transcription("hello world", "hello world")
    assert result["score"] == 1.0
    assert "LLM error" in result["feedback"]
    assert result["suggestions"] == []


# ---------------------------------------------------------------------------
# _categorize_phrase
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("def fibonacci function", "programming"),
        ("class inheritance method", "programming"),
        ("hey computer turn on the lights", "voice_commands"),
        ("create a python tool", "creation_commands"),
        ("hello world", "simple"),  # <= 3 words, no keyword
        ("the quick brown fox jumps over", "complex"),
    ],
)
def test_categorize_phrase(fake_transcriber, phrase, expected):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    assert tester._categorize_phrase(phrase) == expected


# ---------------------------------------------------------------------------
# run_comprehensive_test
# ---------------------------------------------------------------------------


def test_run_comprehensive_test_aggregates(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(
            fake_transcriber,
            test_phrases=["hello world", "def fibonacci function"],
        )

    # Force deterministic transcription accuracy + llm judge.
    with patch.object(
        tester, "test_transcription_accuracy", return_value=("trans", 0.5)
    ), patch.object(
        tester,
        "llm_judge_transcription",
        return_value={
            "score": 0.8,
            "feedback": "ok",
            "suggestions": ["improve a", "improve a", "improve b"],
            "error_pattern": "ep",
            "semantic_preservation": False,
        },
    ):
        results = tester.run_comprehensive_test()

    assert results["total_tests"] == 2
    assert len(results["individual_results"]) == 2
    assert abs(results["summary"]["average_accuracy"] - 0.8) < 1e-9
    # two categories: simple + programming, both average 0.8 -> max/min still set
    assert results["summary"]["best_category"] in {"simple", "programming"}
    assert results["summary"]["worst_category"] in {"simple", "programming"}
    # suggestion aggregation sorted by frequency desc
    suggestions = results["summary"]["improvement_suggestions"]
    assert suggestions[0]["frequency"] >= suggestions[-1]["frequency"]
    first = results["individual_results"][0]
    assert first["transcription"] == "trans"
    assert first["basic_accuracy"] == 0.5
    assert first["llm_score"] == 0.8
    assert first["semantic_preservation"] is False


def test_init_empty_phrase_list_falls_back_to_defaults(fake_transcriber):
    # NOTE: current behavior — an empty list is falsy, so `test_phrases or
    # self._get_default_test_phrases()` substitutes the defaults. Callers
    # cannot force "zero phrases" via the constructor argument.
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber, test_phrases=[])
    assert tester.test_phrases == tester._get_default_test_phrases()


def test_run_comprehensive_test_empty_phrases(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber, test_phrases=["x"])
    # Set to an empty list post-construction to drive the no-results branches.
    tester.test_phrases = []
    results = tester.run_comprehensive_test()
    assert results["total_tests"] == 0
    assert results["summary"]["average_accuracy"] == 0.0
    assert results["summary"]["best_category"] == ""
    assert results["summary"]["worst_category"] == ""


def test_run_comprehensive_test_missing_suggestions_key(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber, test_phrases=["hello world"])
    with patch.object(
        tester, "test_transcription_accuracy", return_value=("t", 0.4)
    ), patch.object(
        tester, "llm_judge_transcription", return_value={"score": 0.6}
    ):
        results = tester.run_comprehensive_test()
    # No "suggestions" key -> no aggregation, llm_score taken from result.
    assert results["summary"]["improvement_suggestions"] == []
    assert results["individual_results"][0]["llm_score"] == 0.6


# ---------------------------------------------------------------------------
# suggest_improvements
# ---------------------------------------------------------------------------


def test_suggest_improvements_low_accuracy(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    results = {
        "summary": {
            "average_accuracy": 0.5,
            "worst_category": "programming",
            "improvement_suggestions": [
                {"suggestion": "s1", "frequency": 3},
                {"suggestion": "s2", "frequency": 2},
                {"suggestion": "s3", "frequency": 1},
                {"suggestion": "s4", "frequency": 1},
            ],
        }
    }
    suggestions = tester.suggest_improvements(results)
    text = "\n".join(suggestions)
    assert "higher-quality transcription backend" in text
    assert "domain-specific vocabulary" in text  # < 0.9 branch
    assert "programming" in text
    # only top 3 llm suggestions
    assert "Frequent issue: s1" in text
    assert "Frequent issue: s4" not in text


def test_suggest_improvements_high_accuracy_minimal(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    results = {"summary": {"average_accuracy": 0.95}}
    suggestions = tester.suggest_improvements(results)
    # >= 0.9 and no worst_category, no llm suggestions -> empty list
    assert suggestions == []


def test_suggest_improvements_mid_accuracy(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    results = {"summary": {"average_accuracy": 0.8}}
    suggestions = tester.suggest_improvements(results)
    # >=0.7 so no backend switch; <0.9 so vocabulary suggestion present
    assert any("domain-specific vocabulary" in s for s in suggestions)
    assert not any("higher-quality transcription backend" in s for s in suggestions)


# ---------------------------------------------------------------------------
# auto_tune_parameters
# ---------------------------------------------------------------------------


def test_auto_tune_low_accuracy_switches_backend(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    rec = tester.auto_tune_parameters({"summary": {"average_accuracy": 0.5}})
    assert rec["transcription_backend"] == "whisper_api"


def test_auto_tune_high_accuracy_keeps_current(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    rec = tester.auto_tune_parameters({"summary": {"average_accuracy": 0.95}})
    assert rec["transcription_backend"] == "current"


def test_auto_tune_timeout_and_preprocessing(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    results = {
        "summary": {"average_accuracy": 0.95},
        "individual_results": [
            {"feedback": "timeout occurred, too much noise"},
            {"feedback": "volume too quiet and fast speed"},
            {"feedback": "fine"},
        ],
    }
    rec = tester.auto_tune_parameters(results)
    # 1 of 3 timeout issues = 33% > 20%
    assert rec["record_timeout"] == "increase"
    assert rec["silence_timeout"] == "increase"
    pre = set(rec["preprocessing"])
    assert {"noise_reduction", "volume_normalization", "speed_normalization"} <= pre


def test_auto_tune_no_timeout_issues(fake_transcriber):
    with patch.object(st, "TTS_AVAILABLE", False):
        tester = make_tester(fake_transcriber)
    results = {
        "summary": {"average_accuracy": 0.95},
        "individual_results": [{"feedback": "fine"}],
    }
    rec = tester.auto_tune_parameters(results)
    assert rec["record_timeout"] == "current"
    assert rec["silence_timeout"] == "current"
    assert rec["preprocessing"] == []


# ---------------------------------------------------------------------------
# create_self_improvement_loop
# ---------------------------------------------------------------------------


def test_create_self_improvement_loop(fake_transcriber):
    fake_results = {
        "summary": {
            "average_accuracy": 0.7,
            "best_category": "simple",
            "worst_category": "programming",
        }
    }
    with patch.object(st, "VoiceSelfTester") as Tester, patch.object(
        st.time, "sleep"
    ) as sleep:
        inst = Tester.return_value
        inst.run_comprehensive_test.return_value = fake_results
        inst.suggest_improvements.return_value = ["s"]
        inst.auto_tune_parameters.return_value = {"transcription_backend": "current"}

        out = create_self_improvement_loop(
            transcriber=fake_transcriber, iterations=2
        )

    assert out["total_iterations"] == 2
    assert len(out["improvement_history"]) == 2
    assert out["final_accuracy"] == 0.7
    assert out["accuracy_trend"] == [0.7, 0.7]
    assert sleep.call_count == 2


def test_create_self_improvement_loop_zero_iterations(fake_transcriber):
    with patch.object(st, "VoiceSelfTester"), patch.object(st.time, "sleep"):
        out = create_self_improvement_loop(
            transcriber=fake_transcriber, iterations=0
        )
    assert out["total_iterations"] == 0
    assert out["improvement_history"] == []
    assert out["final_accuracy"] == 0.0
    assert out["accuracy_trend"] == []


# ---------------------------------------------------------------------------
# add_self_test_commands (CLI wiring)
# ---------------------------------------------------------------------------


def test_add_self_test_commands_parses_run():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_self_test_commands(subparsers)
    args = parser.parse_args(
        ["self-test", "run", "--openai-key", "k", "--phrases", "a", "b"]
    )
    assert args.command == "self-test"
    assert args.test_command == "run"
    assert args.openai_key == "k"
    assert args.phrases == ["a", "b"]


def test_add_self_test_commands_parses_improve_and_benchmark():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_self_test_commands(subparsers)

    improve = parser.parse_args(["self-test", "improve", "--iterations", "7"])
    assert improve.test_command == "improve"
    assert improve.iterations == 7

    bench = parser.parse_args(
        ["self-test", "benchmark", "--save-results", "/tmp/x.json"]
    )
    assert bench.test_command == "benchmark"
    assert bench.save_results == "/tmp/x.json"


# ---------------------------------------------------------------------------
# handle_self_test_command (dispatch + output)
# ---------------------------------------------------------------------------


def test_handle_no_test_command(capsys):
    handle_self_test_command(SimpleNamespace(test_command=None))
    out = capsys.readouterr().out
    assert "No self-test command specified" in out


def test_handle_missing_attribute(capsys):
    # args without test_command attribute at all
    handle_self_test_command(SimpleNamespace())
    out = capsys.readouterr().out
    assert "No self-test command specified" in out


def test_handle_tts_unavailable(capsys):
    args = SimpleNamespace(test_command="run")
    with patch.object(st, "TTS_AVAILABLE", False):
        handle_self_test_command(args)
    out = capsys.readouterr().out
    assert "TTS not available" in out


def test_handle_run_success(capsys):
    args = SimpleNamespace(test_command="run", openai_key=None, phrases=["hello world"])
    fake_results = {
        "summary": {
            "average_accuracy": 0.85,
            "best_category": "simple",
            "worst_category": "complex",
        }
    }
    fake_tester = MagicMock()
    fake_tester.run_comprehensive_test.return_value = fake_results
    fake_tester.suggest_improvements.return_value = ["do x", "do y"]
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "VoiceSelfTester", return_value=fake_tester
    ) as Tester:
        handle_self_test_command(args)
    Tester.assert_called_once_with(openai_api_key=None, test_phrases=["hello world"])
    out = capsys.readouterr().out
    assert "Running voice self-test" in out
    assert "85" in out
    assert "do x" in out


def test_handle_run_no_suggestions(capsys):
    args = SimpleNamespace(test_command="run", openai_key=None, phrases=None)
    fake_tester = MagicMock()
    fake_tester.run_comprehensive_test.return_value = {
        "summary": {
            "average_accuracy": 0.99,
            "best_category": "simple",
            "worst_category": "simple",
        }
    }
    fake_tester.suggest_improvements.return_value = []
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "VoiceSelfTester", return_value=fake_tester
    ):
        handle_self_test_command(args)
    out = capsys.readouterr().out
    assert "Improvement suggestions" not in out


def test_handle_improve(capsys):
    args = SimpleNamespace(test_command="improve", openai_key="k", iterations=2)
    loop_result = {"final_accuracy": 0.77, "accuracy_trend": [0.7, 0.77]}
    fake_transcriber = MagicMock()
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "VoiceTranscriber", return_value=fake_transcriber
    ) as VT, patch.object(
        st, "create_self_improvement_loop", return_value=loop_result
    ) as loop:
        handle_self_test_command(args)
    VT.assert_called_once_with(backend="whisper_local")
    loop.assert_called_once_with(
        transcriber=fake_transcriber, openai_api_key="k", iterations=2
    )
    out = capsys.readouterr().out
    assert "Improvement Results" in out
    assert "77" in out


def test_handle_benchmark_with_save(capsys, tmp_path):
    save_path = tmp_path / "results.json"
    args = SimpleNamespace(
        test_command="benchmark", openai_key=None, save_results=str(save_path)
    )
    fake_results = {"summary": {"average_accuracy": 0.9}}
    fake_tester = MagicMock()
    fake_tester.run_comprehensive_test.return_value = fake_results
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "VoiceSelfTester", return_value=fake_tester
    ):
        handle_self_test_command(args)
    out = capsys.readouterr().out
    assert "Benchmark complete" in out
    assert "saved to" in out
    assert json.loads(save_path.read_text())["summary"]["average_accuracy"] == 0.9


def test_handle_benchmark_no_save(capsys):
    args = SimpleNamespace(test_command="benchmark", openai_key=None, save_results=None)
    fake_tester = MagicMock()
    fake_tester.run_comprehensive_test.return_value = {
        "summary": {"average_accuracy": 0.6}
    }
    with patch.object(st, "TTS_AVAILABLE", True), patch.object(
        st, "VoiceSelfTester", return_value=fake_tester
    ):
        handle_self_test_command(args)
    out = capsys.readouterr().out
    assert "Benchmark complete" in out
    assert "saved to" not in out


def test_handle_unknown_command_no_output(capsys):
    # An unrecognized test_command falls through all branches silently.
    args = SimpleNamespace(test_command="bogus")
    with patch.object(st, "TTS_AVAILABLE", True):
        handle_self_test_command(args)
    out = capsys.readouterr().out
    assert out == ""
