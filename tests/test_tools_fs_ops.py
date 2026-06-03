import json
from pathlib import Path
from chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text

def test_ensure_dir(tmp_path: Path):
    """Test that ensure_dir creates a directory and handles existing ones."""
    test_path = tmp_path / "new_dir"
    assert not test_path.exists()

    # Test creation
    ensure_dir(test_path)
    assert test_path.is_dir()

    # Test existing (should not raise error)
    ensure_dir(test_path)
    assert test_path.is_dir()

    # Test nested creation
    nested_path = tmp_path / "nested" / "dir"
    assert not nested_path.exists()
    ensure_dir(nested_path)
    assert nested_path.is_dir()


def test_write_json(tmp_path: Path):
    """Test that write_json writes data and creates parent directories."""
    json_path = tmp_path / "subdir" / "test.json"
    data = {"key": "value", "number": 42}

    assert not json_path.parent.exists()

    write_json(json_path, data)

    assert json_path.exists()
    assert json_path.parent.is_dir()

    with json_path.open("r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data == data

    # Verify pretty formatting (indent=2)
    content = json_path.read_text(encoding="utf-8")
    assert '{\n  "key": "value",\n  "number": 42\n}' in content


def test_write_text(tmp_path: Path):
    """Test that write_text writes data and creates parent directories."""
    text_path = tmp_path / "subdir2" / "test.txt"
    content = "Hello, world!\nLine 2"

    assert not text_path.parent.exists()

    write_text(text_path, content)

    assert text_path.exists()
    assert text_path.parent.is_dir()

    assert text_path.read_text(encoding="utf-8") == content
