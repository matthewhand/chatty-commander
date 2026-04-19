"""DefaultConfigGenerator behavior tests."""

import json

from chatty_commander.app.default_config import DefaultConfigGenerator


def test_should_generate_default_config_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = DefaultConfigGenerator()

    assert generator.should_generate_default_config() is True


def test_should_generate_default_config_with_missing_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"commands": {}}))

    generator = DefaultConfigGenerator()

    assert generator.should_generate_default_config() is True


def test_should_generate_default_config_when_models_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"commands": {}, "state_models": {}}))
    models_idle = tmp_path / "models-idle"
    models_idle.mkdir()
    (models_idle / "dummy.onnx").write_text("data")

    generator = DefaultConfigGenerator()

    assert generator.should_generate_default_config() is False


def test_generate_default_config_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = DefaultConfigGenerator()

    generator.generate_default_config()

    config_path = tmp_path / "config.json"
    wakewords_dir = tmp_path / "wakewords"

    assert config_path.exists()
    assert wakewords_dir.exists()
    assert any(wakewords_dir.iterdir())

    generated = json.loads(config_path.read_text())
    assert "commands" in generated
    assert "state_models" in generated
