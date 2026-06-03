import json
from pathlib import Path
from chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text

def test_ensure_dir_creates_new_dir(tmp_path: Path):
    path = tmp_path / "new_dir"
    assert not path.exists()
    ensure_dir(path)
    assert path.exists()
    assert path.is_dir()

def test_ensure_dir_creates_nested_dir(tmp_path: Path):
    path = tmp_path / "parent" / "child" / "grandchild"
    assert not path.exists()
    ensure_dir(path)
    assert path.exists()
    assert path.is_dir()

def test_ensure_dir_handles_existing_dir(tmp_path: Path):
    path = tmp_path / "existing_dir"
    path.mkdir()
    assert path.exists()
    # Should not raise an exception
    ensure_dir(path)
    assert path.exists()
    assert path.is_dir()

def test_write_json_creates_file_and_parent_dirs(tmp_path: Path):
    path = tmp_path / "nested" / "data.json"
    data = {"key": "value", "nested": {"a": 1}}

    write_json(path, data)

    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data

def test_write_text_creates_file_and_parent_dirs(tmp_path: Path):
    path = tmp_path / "nested" / "test.txt"
    content = "Hello, World!\nLine 2"

    write_text(path, content)

    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        loaded_content = f.read()
    assert loaded_content == content
