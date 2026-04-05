import pytest
from pathlib import Path
import json
from chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text

def test_ensure_dir(tmp_path):
    target = tmp_path / "new_dir"
    ensure_dir(target)
    assert target.is_dir()
    # Test idempotency
    ensure_dir(target)
    assert target.is_dir()

def test_write_json(tmp_path):
    target = tmp_path / "data" / "file.json"
    data = {"key": "value"}
    write_json(target, data)
    
    assert target.is_file()
    with target.open() as f:
        loaded = json.load(f)
    assert loaded == data

def test_write_text(tmp_path):
    target = tmp_path / "data" / "file.txt"
    text = "Hello, World!"
    write_text(target, text)
    
    assert target.is_file()
    with target.open() as f:
        loaded = f.read()
    assert loaded == text
