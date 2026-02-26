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

import json
from pathlib import Path

from chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text


def test_ensure_dir_creates_directory(tmp_path: Path):
    target_dir = tmp_path / "new_dir"
    ensure_dir(target_dir)
    assert target_dir.is_dir()


def test_ensure_dir_existing_directory(tmp_path: Path):
    target_dir = tmp_path / "existing_dir"
    target_dir.mkdir()
    ensure_dir(target_dir)  # Should not raise error
    assert target_dir.is_dir()


def test_ensure_dir_nested(tmp_path: Path):
    target_dir = tmp_path / "nested" / "dir"
    ensure_dir(target_dir)
    assert target_dir.is_dir()


def test_write_json_creates_file(tmp_path: Path):
    target_file = tmp_path / "data.json"
    data = {"key": "value", "number": 123}
    write_json(target_file, data)

    assert target_file.is_file()
    with target_file.open("r", encoding="utf-8") as f:
        content = json.load(f)
    assert content == data


def test_write_json_creates_parent_dirs(tmp_path: Path):
    target_file = tmp_path / "nested" / "data.json"
    data = {"key": "value"}
    write_json(target_file, data)

    assert target_file.is_file()
    with target_file.open("r", encoding="utf-8") as f:
        content = json.load(f)
    assert content == data


def test_write_json_overwrites(tmp_path: Path):
    target_file = tmp_path / "data.json"
    initial_data = {"old": "data"}
    write_json(target_file, initial_data)

    new_data = {"new": "data"}
    write_json(target_file, new_data)

    with target_file.open("r", encoding="utf-8") as f:
        content = json.load(f)
    assert content == new_data


def test_write_text_creates_file(tmp_path: Path):
    target_file = tmp_path / "file.txt"
    content = "Hello, world!"
    write_text(target_file, content)

    assert target_file.is_file()
    assert target_file.read_text(encoding="utf-8") == content


def test_write_text_creates_parent_dirs(tmp_path: Path):
    target_file = tmp_path / "nested" / "file.txt"
    content = "Nested content"
    write_text(target_file, content)

    assert target_file.is_file()
    assert target_file.read_text(encoding="utf-8") == content


def test_write_text_overwrites(tmp_path: Path):
    target_file = tmp_path / "file.txt"
    initial_content = "Old content"
    write_text(target_file, initial_content)

    new_content = "New content"
    write_text(target_file, new_content)

    assert target_file.read_text(encoding="utf-8") == new_content
