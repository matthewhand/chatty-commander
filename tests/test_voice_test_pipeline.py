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

"""Unit tests for the dry-run voice-test pipeline (ROADMAP P2)."""

from __future__ import annotations

from chatty_commander.app.voice_test_pipeline import (
    MAX_AUDIO_BUFFER_BYTES,
    VoiceTestPipeline,
    describe_dry_run,
    match_command,
    stage_event,
)

MODEL_ACTIONS = {
    "screenshot": {"action": "keypress", "keys": "ctrl+shift+x"},
    "open_jellyfin": {"action": "url", "url": "https://example.com/jellyfin"},
    "play": {"action": "custom_message", "message": "playing"},
}


class DummyConfigManager:
    model_actions = MODEL_ACTIONS


class FakeTranscriber:
    def __init__(self, text: str) -> None:
        self.text = text
        self.received: list[bytes] = []

    def transcribe_audio_data(self, audio: bytes) -> str:
        self.received.append(audio)
        return self.text


# ---------------------------------------------------------------- stage_event


def test_stage_event_shape():
    ev = stage_event("match", {"matched": True})
    assert set(ev) == {"stage", "data", "ts"}
    assert ev["stage"] == "match"
    assert ev["data"] == {"matched": True}
    assert isinstance(ev["ts"], str) and "T" in ev["ts"]


# -------------------------------------------------------------- match_command


def test_match_command_direct_name():
    assert match_command("take a screenshot now", MODEL_ACTIONS) == "screenshot"


def test_match_command_underscore_name_as_phrase():
    assert match_command("please open jellyfin", MODEL_ACTIONS) == "open_jellyfin"


def test_match_command_no_substring_false_positive():
    # "replay" must not whole-word match command "play"
    assert match_command("watch the replay", MODEL_ACTIONS) is None


def test_match_command_unknown_text():
    assert match_command("completely unrelated words", MODEL_ACTIONS) is None


def test_match_command_empty_inputs():
    assert match_command("", MODEL_ACTIONS) is None
    assert match_command("screenshot", {}) is None
    assert match_command("screenshot", None) is None  # type: ignore[arg-type]


def test_match_command_keyword_alias():
    actions = {"lights": {"action": "shell", "cmd": "lights-on"}}
    assert match_command("turn on the lamp", actions) == "lights"


# ------------------------------------------------------------ describe_dry_run


def test_describe_keypress_string_and_list():
    assert (
        describe_dry_run("screenshot", {"action": "keypress", "keys": "ctrl+shift+x"})
        == "would press ctrl+shift+x"
    )
    assert (
        describe_dry_run("s", {"action": "keypress", "keys": ["ctrl", "c"]})
        == "would press ctrl+c"
    )


def test_describe_url_and_shell_and_message():
    assert (
        describe_dry_run("j", {"action": "url", "url": "https://example.com"})
        == "would open https://example.com"
    )
    assert (
        describe_dry_run("c", {"action": "shell", "cmd": "ls -la"})
        == "would run shell command: ls -la"
    )
    assert (
        describe_dry_run("m", {"action": "custom_message", "message": "hi"})
        == "would display message: hi"
    )


def test_describe_voice_chat_and_dograh():
    assert describe_dry_run("v", {"action": "voice_chat"}) == (
        "would start a voice chat session"
    )
    assert (
        describe_dry_run("d", {"action": "dograh_call", "workflow_id": 42})
        == "would place dograh call (workflow 42)"
    )


def test_describe_legacy_formats():
    assert describe_dry_run("k", {"keypress": "alt+f4"}) == "would press alt+f4"
    assert describe_dry_run("u", {"url": "http://x"}) == "would open http://x"
    assert describe_dry_run("s", {"shell": "echo hi"}) == (
        "would run shell command: echo hi"
    )


def test_describe_unknown_shapes_fall_back():
    assert "would execute command 'x'" == describe_dry_run("x", {"action": "bogus"})
    assert "would execute command 'x'" == describe_dry_run("x", "not-a-dict")


# ----------------------------------------------------------- VoiceTestPipeline


def test_process_text_match_emits_transcript_match_action():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    events = p.process_text("take a screenshot")
    stages = [e["stage"] for e in events]
    assert stages == ["transcript", "match", "action"]
    assert events[0]["data"] == {"text": "take a screenshot", "simulated": True}
    assert events[1]["data"] == {"matched": True, "command": "screenshot"}
    action = events[2]["data"]
    assert action["dry_run"] is True
    assert action["executed"] is False
    assert action["description"] == "would press ctrl+shift+x"


def test_process_text_no_match():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    events = p.process_text("nothing relevant here")
    assert [e["stage"] for e in events] == ["transcript", "match"]
    assert events[1]["data"]["matched"] is False


def test_process_text_without_config_manager():
    p = VoiceTestPipeline(config_manager=None)
    events = p.process_text("screenshot")
    assert events[-1]["stage"] == "match"
    assert events[-1]["data"]["matched"] is False


def test_start_event_reports_dry_run_and_sample_rate():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    ev = p.start(sample_rate=48000)
    assert ev["stage"] == "listening"
    assert ev["data"]["dry_run"] is True
    assert ev["data"]["sample_rate"] == 48000
    assert isinstance(ev["data"]["transcription_available"], bool)


def test_start_rejects_silly_sample_rates():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    ev = p.start(sample_rate=1)
    assert ev["data"]["sample_rate"] == 16000


def test_finish_audio_without_audio_is_error():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    events = p.finish_audio()
    assert events[0]["stage"] == "error"
    assert events[0]["data"]["code"] == "no_audio"


def test_finish_audio_without_backend_degrades_gracefully():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    # Force "resolved, unavailable" regardless of host audio stack.
    p._transcriber_resolved = True
    p._transcriber = None
    p.feed_audio(b"\x00\x01" * 100)
    events = p.finish_audio()
    assert events[0]["stage"] == "error"
    assert events[0]["data"]["code"] == "transcription_unavailable"


def test_finish_audio_with_injected_transcriber_runs_full_pipeline():
    t = FakeTranscriber("open jellyfin please")
    p = VoiceTestPipeline(config_manager=DummyConfigManager(), transcriber=t)
    p.feed_audio(b"\x00\x01" * 100)
    events = p.finish_audio()
    assert [e["stage"] for e in events] == ["transcript", "match", "action"]
    assert events[0]["data"]["simulated"] is False
    assert events[1]["data"]["command"] == "open_jellyfin"
    assert events[2]["data"]["description"] == "would open https://example.com/jellyfin"
    assert t.received == [b"\x00\x01" * 100]


def test_finish_audio_transcriber_exception_is_error_event():
    class Boom:
        def transcribe_audio_data(self, audio: bytes) -> str:
            raise RuntimeError("kaput")

    p = VoiceTestPipeline(config_manager=DummyConfigManager(), transcriber=Boom())
    p.feed_audio(b"abc")
    events = p.finish_audio()
    assert events[0]["stage"] == "error"
    assert events[0]["data"]["code"] == "transcription_failed"


def test_feed_audio_buffer_cap():
    p = VoiceTestPipeline(config_manager=DummyConfigManager())
    assert p.feed_audio(b"x" * MAX_AUDIO_BUFFER_BYTES) is None
    over = p.feed_audio(b"y")
    assert over is not None
    assert over["stage"] == "error"
    assert over["data"]["code"] == "audio_buffer_full"
