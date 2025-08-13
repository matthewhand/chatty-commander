import json
import os

from chatty_commander.app.config import Config


def test_config_env_endpoint_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")

    monkeypatch.setenv("CHATBOT_ENDPOINT", "http://override.local/")
    monkeypatch.setenv("HOME_ASSISTANT_ENDPOINT", "http://ha.local/api")

    c = Config(config_file=str(cfg_path))
    assert c.api_endpoints["chatbot_endpoint"] == "http://override.local/"
    assert c.api_endpoints["home_assistant"] == "http://ha.local/api"


def test_config_env_audio_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "audio_settings": {
                    "mic_chunk_size": 512,
                    "sample_rate": 8000,
                    "audio_format": "int8",
                }
            }
        )
    )

    monkeypatch.setenv("CHATCOMM_MIC_CHUNK_SIZE", "2048")
    monkeypatch.setenv("CHATCOMM_SAMPLE_RATE", "44100")
    monkeypatch.setenv("CHATCOMM_AUDIO_FORMAT", "float32")

    c = Config(config_file=str(cfg_path))
    c.save_config()
    assert c.mic_chunk_size == 2048
    assert c.sample_rate == 44100
    assert c.audio_format == "float32"


def test_config_env_audio_invalid(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps({"audio_settings": {"mic_chunk_size": 512, "sample_rate": 8000}})
    )

    monkeypatch.setenv("CHATCOMM_MIC_CHUNK_SIZE", "not-a-number")
    monkeypatch.setenv("CHATCOMM_SAMPLE_RATE", "-1")

    c = Config(config_file=str(cfg_path))
    c.save_config()
    assert c.mic_chunk_size == 512
    assert c.sample_rate == 8000
