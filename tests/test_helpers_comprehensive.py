"""Comprehensive tests for helpers module with proper cleanup and edge cases."""

from pathlib import Path

import pytest

from chatty_commander.app.helpers import (
    ensure_directory_exists,
    format_command_output,
    parse_model_keybindings,
)


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists with proper cleanup and edge cases."""

    def test_creates_missing_directory(self, tmp_path: Path) -> None:
        """Test that a missing directory is created."""
        test_dir = tmp_path / "new_dir"
        assert not test_dir.exists()

        ensure_directory_exists(str(test_dir))

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_handles_existing_directory(self, tmp_path: Path) -> None:
        """Test that an existing directory is handled gracefully."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        assert test_dir.exists()

        # Should not raise
        ensure_directory_exists(str(test_dir))

        assert test_dir.exists()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Test creation of nested directory paths."""
        test_dir = tmp_path / "a" / "b" / "c" / "d"

        ensure_directory_exists(str(test_dir))

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_handles_empty_path(self) -> None:
        """Test that empty string is handled (current directory always exists)."""
        # Empty path should not raise - os.makedirs("") raises FileExistsError
        # but os.path.exists("") returns False, so we skip creation
        ensure_directory_exists("")

    def test_handles_relative_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that relative paths work correctly."""
        monkeypatch.chdir(tmp_path)
        test_dir = "relative_dir"

        ensure_directory_exists(test_dir)

        assert (tmp_path / test_dir).exists()


class TestFormatCommandOutput:
    """Tests for format_command_output."""

    def test_formats_multiline_output(self) -> None:
        """Test that newlines are replaced with pipes."""
        output = "Line1\nLine2\nLine3"
        result = format_command_output(output)
        assert result == "Line1 | Line2 | Line3"

    def test_strips_leading_trailing_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        output = "  \nLine1\nLine2\n  "
        result = format_command_output(output)
        assert result == "Line1 | Line2"

    def test_handles_empty_string(self) -> None:
        """Test empty input returns empty output."""
        result = format_command_output("")
        assert result == ""

    def test_handles_single_line(self) -> None:
        """Test single line is just stripped."""
        output = "  single line  "
        result = format_command_output(output)
        assert result == "single line"

    def test_preserves_internal_spaces(self) -> None:
        """Test that internal spaces are preserved."""
        output = "Line with  spaces\nAnother line"
        result = format_command_output(output)
        assert result == "Line with  spaces | Another line"


class TestParseModelKeybindings:
    """Tests for parse_model_keybindings."""

    def test_parses_single_keybinding(self) -> None:
        """Test parsing a single keybinding pair."""
        result = parse_model_keybindings("model1=ctrl+shift+1")
        assert result == {"model1": "ctrl+shift+1"}

    def test_parses_multiple_keybindings(self) -> None:
        """Test parsing multiple keybinding pairs."""
        result = parse_model_keybindings("model1=ctrl+shift+1,model2=alt+F4,model3=ctrl+A")
        assert result == {
            "model1": "ctrl+shift+1",
            "model2": "alt+F4",
            "model3": "ctrl+A",
        }

    def test_handles_empty_string(self) -> None:
        """Test that empty string returns empty dict."""
        result = parse_model_keybindings("")
        assert result == {}

    def test_strips_whitespace(self) -> None:
        """Test that whitespace around keys and values is stripped."""
        result = parse_model_keybindings(" model1 = ctrl+shift+1 , model2 = alt+F4 ")
        assert result == {"model1": "ctrl+shift+1", "model2": "alt+F4"}

    def test_handles_equals_in_value(self) -> None:
        """Test that equals signs in values are preserved."""
        result = parse_model_keybindings("model1=key=value")
        assert result == {"model1": "key=value"}

    def test_handles_empty_value(self) -> None:
        """Test handling of empty value after equals."""
        result = parse_model_keybindings("model1=")
        assert result == {"model1": ""}
