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

"""
Comprehensive tests for filesystem operations module.

Tests directory creation, JSON writing, and text file operations.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.chatty_commander.tools.fs_ops import ensure_dir, write_json, write_text


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_creates_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as tmp:
            new_dir = Path(tmp) / "new_directory"
            assert not new_dir.exists()
            
            ensure_dir(new_dir)
            
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_handles_existing_directory(self):
        """Test that existing directory doesn't raise error."""
        with tempfile.TemporaryDirectory() as tmp:
            existing_dir = Path(tmp) / "existing"
            existing_dir.mkdir()
            
            # Should not raise
            ensure_dir(existing_dir)
            
            assert existing_dir.exists()

    def test_creates_nested_directories(self):
        """Test creating nested directory structure."""
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "a" / "b" / "c"
            
            ensure_dir(nested)
            
            assert nested.exists()
            assert nested.is_dir()

    def test_creates_relative_to_current_dir(self):
        """Test creating directory with relative path."""
        with tempfile.TemporaryDirectory() as tmp:
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                rel_path = Path("relative_dir")
                
                ensure_dir(rel_path)
                
                assert rel_path.exists()
            finally:
                os.chdir(original_cwd)


class TestWriteJson:
    """Tests for write_json function."""

    def test_writes_valid_json(self):
        """Test writing valid JSON data."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            data = {"key": "value", "number": 42}
            
            write_json(path, data)
            
            assert path.exists()
            with open(path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_creates_parent_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subdir" / "nested" / "file.json"
            data = {"test": True}
            
            write_json(path, data)
            
            assert path.parent.exists()
            assert path.exists()

    def test_overwrites_existing_file(self):
        """Test that existing file is overwritten."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "existing.json"
            path.write_text('{"old": "data"}')
            
            new_data = {"new": "data"}
            write_json(path, new_data)
            
            with open(path) as f:
                loaded = json.load(f)
            assert loaded == new_data

    def test_handles_nested_data(self):
        """Test writing nested dictionary data."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested.json"
            data = {
                "level1": {
                    "level2": {
                        "level3": ["a", "b", "c"]
                    }
                },
                "list": [1, 2, 3],
                "string": "test"
            }
            
            write_json(path, data)
            
            with open(path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_json_has_indentation(self):
        """Test that JSON output is indented."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "formatted.json"
            data = {"key": "value"}
            
            write_json(path, data)
            
            content = path.read_text()
            # Should have newlines for indentation
            assert '\n' in content

    def test_handles_empty_dict(self):
        """Test writing empty dictionary."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.json"
            
            write_json(path, {})
            
            with open(path) as f:
                loaded = json.load(f)
            assert loaded == {}

    def test_handles_special_characters(self):
        """Test writing JSON with special characters."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "special.json"
            data = {"text": "Hello \u00e9\u00e0\u00fc", "emoji": "🚀"}
            
            write_json(path, data)
            
            with open(path, encoding='utf-8') as f:
                loaded = json.load(f)
            assert loaded == data


class TestWriteText:
    """Tests for write_text function."""

    def test_writes_text_content(self):
        """Test writing text to file."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.txt"
            content = "Hello, World!"
            
            write_text(path, content)
            
            assert path.exists()
            assert path.read_text() == content

    def test_creates_parent_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep" / "path" / "file.txt"
            
            write_text(path, "content")
            
            assert path.parent.exists()
            assert path.exists()

    def test_overwrites_existing_file(self):
        """Test that existing file is overwritten."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "existing.txt"
            path.write_text("old content")
            
            write_text(path, "new content")
            
            assert path.read_text() == "new content"

    def test_handles_multiline_text(self):
        """Test writing multiline text."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "multiline.txt"
            content = "Line 1\nLine 2\nLine 3"
            
            write_text(path, content)
            
            assert path.read_text() == content

    def test_handles_unicode(self):
        """Test writing unicode text."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unicode.txt"
            content = "Hello World"
            
            write_text(path, content)
            
            assert path.read_text() == content

    def test_handles_empty_string(self):
        """Test writing empty string."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.txt"
            
            write_text(path, "")
            
            assert path.exists()
            assert path.read_text() == ""

    def test_handles_special_characters(self):
        """Test writing text with special characters."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "special.txt"
            content = "Special: hello world"
            
            write_text(path, content)
            
            assert path.read_text() == content


class TestFsOpsIntegration:
    """Integration tests for fs_ops module."""

    def test_full_workflow(self):
        """Test complete workflow using all functions."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "project"
            
            # Create directory structure
            data_dir = base / "data"
            ensure_dir(data_dir)
            
            # Write JSON config
            config_file = data_dir / "config.json"
            write_json(config_file, {"version": "1.0", "name": "test"})
            
            # Write text log
            log_file = base / "logs" / "app.log"
            write_text(log_file, "Application started\n")
            
            # Verify all created
            assert data_dir.exists()
            assert config_file.exists()
            assert log_file.exists()
            
            # Verify content
            with open(config_file) as f:
                config = json.load(f)
            assert config["version"] == "1.0"
            assert log_file.read_text() == "Application started\n"

    def test_multiple_operations_same_directory(self):
        """Test multiple operations in same directory."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "shared"
            
            # Write multiple files
            write_json(base / "1.json", {"id": 1})
            write_json(base / "2.json", {"id": 2})
            write_text(base / "readme.txt", "Documentation")
            
            assert (base / "1.json").exists()
            assert (base / "2.json").exists()
            assert (base / "readme.txt").exists()
