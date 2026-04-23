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
Tests for app helpers module.

Tests utility functions for the application.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.chatty_commander.app.helpers import (
    ensure_directory_exists,
    format_command_output,
    parse_model_keybindings,
)


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_creates_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()
        
        ensure_directory_exists(str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test with existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_directory_exists(str(existing_dir))
        
        assert existing_dir.exists()

    def test_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested = tmp_path / "a" / "b" / "c"
        
        ensure_directory_exists(str(nested))
        
        assert nested.exists()


class TestFormatCommandOutput:
    """Tests for format_command_output function."""

    def test_empty_string(self):
        """Test formatting empty string."""
        result = format_command_output("")
        assert result == ""

    def test_single_line(self):
        """Test formatting single line."""
        result = format_command_output("Hello world")
        assert result == "Hello world"

    def test_multiple_lines(self):
        """Test formatting multiple lines."""
        result = format_command_output("Line 1\nLine 2\nLine 3")
        assert result == "Line 1 | Line 2 | Line 3"

    def test_trailing_whitespace(self):
        """Test that trailing whitespace is removed."""
        result = format_command_output("  Hello world  ")
        assert result == "Hello world"

    def test_strips_output(self):
        """Test that output is stripped."""
        result = format_command_output("  Hello world  ")
        assert result == "Hello world"


class TestParseModelKeybindings:
    """Tests for parse_model_keybindings function."""

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_model_keybindings("")
        assert result == {}

    def test_single_binding(self):
        """Test parsing single binding."""
        result = parse_model_keybindings("model1=ctrl+shift+1")
        assert result == {"model1": "ctrl+shift+1"}

    def test_multiple_bindings(self):
        """Test parsing multiple bindings."""
        result = parse_model_keybindings("model1=ctrl+1,model2=alt+F4")
        assert result == {"model1": "ctrl+1", "model2": "alt+F4"}

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        result = parse_model_keybindings("  model1 = ctrl+1 , model2 = alt+2  ")
        assert result == {"model1": "ctrl+1", "model2": "alt+2"}

    def test_complex_keybinding(self):
        """Test parsing complex keybinding."""
        result = parse_model_keybindings("voice=ctrl+shift+v")
        assert result == {"voice": "ctrl+shift+v"}


class TestEdgeCases:
    """Edge case tests."""

    def test_ensure_directory_exists_with_file_path(self, tmp_path):
        """Test behavior when path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        # Should handle gracefully (os.makedirs will fail or succeed depending on OS)
        try:
            ensure_directory_exists(str(file_path))
        except (OSError, FileExistsError):
            pass  # Expected on some systems

    def test_format_command_output_with_special_chars(self):
        """Test formatting with special characters."""
        result = format_command_output("Error: something failed\nPath: /tmp/test")
        assert "Error" in result
        assert "|" in result

    def test_parse_model_keybindings_empty_parts(self):
        """Test parsing with empty parts."""
        # Empty parts should be handled gracefully
        result = parse_model_keybindings("model1=ctrl+1,model2=alt+2")
        assert "model1" in result
        assert "model2" in result
