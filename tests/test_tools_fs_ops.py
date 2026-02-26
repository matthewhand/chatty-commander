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


def test_ensure_dir(tmp_path: Path):
    """Test ensure_dir creates a directory if it doesn't exist."""
    dir_path = tmp_path / "test_dir"
    ensure_dir(dir_path)
    assert dir_path.is_dir()


def test_ensure_dir_nested(tmp_path: Path):
    """Test ensure_dir creates nested directories."""
    dir_path = tmp_path / "nested" / "dir"
    ensure_dir(dir_path)
    assert dir_path.is_dir()


def test_ensure_dir_existing(tmp_path: Path):
    """Test ensure_dir works if the directory already exists."""
    dir_path = tmp_path / "existing_dir"
    dir_path.mkdir()
    ensure_dir(dir_path)
    assert dir_path.is_dir()


def test_write_json(tmp_path: Path):
    """Test write_json writes a dictionary to a JSON file."""
    file_path = tmp_path / "test_file.json"
    data = {"key": "value", "number": 123}
    write_json(file_path, data)
    assert file_path.is_file()
    with file_path.open("r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_write_json_nested(tmp_path: Path):
    """Test write_json creates parent directories if needed."""
    file_path = tmp_path / "nested" / "dir" / "test_file.json"
    data = {"key": "value"}
    write_json(file_path, data)
    assert file_path.is_file()
    with file_path.open("r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_write_text(tmp_path: Path):
    """Test write_text writes a string to a text file."""
    file_path = tmp_path / "test_file.txt"
    data = "Hello, world!"
    write_text(file_path, data)
    assert file_path.is_file()
    with file_path.open("r", encoding="utf-8") as f:
        read_data = f.read()
    assert read_data == data


def test_write_text_nested(tmp_path: Path):
    """Test write_text creates parent directories if needed."""
    file_path = tmp_path / "nested" / "dir" / "test_file.txt"
    data = "Hello, nested world!"
    write_text(file_path, data)
    assert file_path.is_file()
    with file_path.open("r", encoding="utf-8") as f:
        read_data = f.read()
    assert read_data == data
