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
