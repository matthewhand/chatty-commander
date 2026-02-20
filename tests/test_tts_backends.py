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

"""Text-to-speech backend tests."""

from unittest.mock import patch

import chatty_commander.voice.tts as tts


def test_mock_tts_backend_records_spoken():
    backend = tts.MockTTSBackend()
    backend.speak("hello")

    assert backend.spoken == ["hello"]


def test_pyttsx3_backend_missing_dependency(monkeypatch):
    monkeypatch.setattr(tts, "pyttsx3", None)

    backend = tts.Pyttsx3Backend()

    assert backend.is_available() is False


def test_pyttsx3_backend_init_failure(monkeypatch):
    class DummyPyttsx3:
        def init(self):
            raise RuntimeError("init failed")

    monkeypatch.setattr(tts, "pyttsx3", DummyPyttsx3())

    backend = tts.Pyttsx3Backend()

    assert backend.is_available() is False


def test_text_to_speech_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr(tts, "pyttsx3", None)

    tts_engine = tts.TextToSpeech(backend="pyttsx3")

    assert isinstance(tts_engine.backend, tts.MockTTSBackend)


def test_text_to_speech_speak_logs_error():
    tts_engine = tts.TextToSpeech(backend="mock")

    with patch.object(tts_engine.backend, "speak", side_effect=RuntimeError("boom")):
        with patch.object(tts, "logger") as logger_mock:
            tts_engine.speak("hello")
            logger_mock.error.assert_called_once()


def test_text_to_speech_backend_info():
    tts_engine = tts.TextToSpeech(backend="mock")

    assert tts_engine.get_backend_info() == {
        "backend_type": "MockTTSBackend",
        "is_available": True,
    }
