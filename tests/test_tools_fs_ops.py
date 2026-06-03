import json
from pathlib import Path
from chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text

def test_ensure_dir(tmp_path: Path):
    """Test ensure_dir creates directory and nested directories."""
    # Test simple directory creation
    path = tmp_path / "test_dir"
    ensure_dir(path)
    assert path.is_dir()

    # Test nested directory creation
    nested_path = tmp_path / "parent" / "child" / "grandchild"
    ensure_dir(nested_path)
    assert nested_path.is_dir()

    # Test existing directory doesn't raise error
    ensure_dir(nested_path)
    assert nested_path.is_dir()

def test_write_json(tmp_path: Path):
    """Test write_json writes data and creates parents if needed."""
    data = {"key": "value", "number": 42}
    json_path = tmp_path / "nested" / "output.json"

    write_json(json_path, data)

    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data

    # Check indentation (optional but part of docstring)
    with open(json_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "  \"key\": \"value\"" in content or "  \"number\": 42" in content

def test_write_text(tmp_path: Path):
    """Test write_text writes data and creates parents if needed."""
    content = "Hello, World!\nThis is a test."
    text_path = tmp_path / "deeply" / "nested" / "file.txt"

    write_text(text_path, content)

    assert text_path.exists()
    with open(text_path, "r", encoding="utf-8") as f:
        loaded_content = f.read()
    assert loaded_content == content
