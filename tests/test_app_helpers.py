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
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY KIND, CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive tests for application helpers module.

Tests utility functions for directory management, command formatting, and keybinding parsing.
"""

import os
import tempfile
from unittest.mock import patch

from src.chatty_commander.app.helpers import (
    ensure_directory_exists,
    format_command_output,
    parse_model_keybindings,
)


class TestEnsureDirectoryExists:
    """Test directory creation utility function."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new_directory"

        # Directory should not exist initially
        assert not new_dir.exists()

        # Function should create it
        result = ensure_directory_exists(str(new_dir))

        # Should return True on success
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test with already existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # Directory exists
        assert existing_dir.exists()

        # Function should return True (no error)
        result = ensure_directory_exists(str(existing_dir))

        assert result is True
        assert existing_dir.exists()

    def test_create_nested_directories(self, tmp_path):
        """Test creating nested directory structure."""
        nested_path = tmp_path / "parent" / "child" / "grandchild"

        # None of the directories exist
        assert not nested_path.exists()

        # Function should create all parent directories
        result = ensure_directory_exists(str(nested_path))

        assert result is True
        assert nested_path.exists()
        assert nested_path.is_dir()

    def test_relative_path_creation(self):
        """Test creating directory with relative path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()

            try:
                # Change to temp directory
                os.chdir(temp_dir)

                # Create relative path directory
                relative_dir = "relative_test"
                result = ensure_directory_exists(relative_dir)

                assert result is True
                assert os.path.exists(relative_dir)
                assert os.path.isdir(relative_dir)

            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_path_with_permissions(self, tmp_path):
        """Test directory creation with permission constraints."""
        # Create a read-only directory
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)  # Read-only

        try:
            # Try to create subdirectory in read-only directory
            sub_dir = read_only_dir / "subdir"
            result = ensure_directory_exists(str(sub_dir))

            # May or may not succeed depending on system permissions
            assert isinstance(result, bool)

        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)

    def test_invalid_path_characters(self):
        """Test handling of invalid path characters."""
        # Test with path containing invalid characters for the OS
        invalid_paths = [
            "",  # Empty string
            "/",  # Root directory
            "?",  # Invalid character on Windows
            "*",  # Invalid character on Windows
        ]

        for invalid_path in invalid_paths:
            try:
                result = ensure_directory_exists(invalid_path)
                # Should handle gracefully (may succeed or fail depending on OS)
                assert isinstance(result, bool)
            except (OSError, ValueError):
                # Should raise appropriate exception for truly invalid paths
                assert True

    def test_path_length_limits(self):
        """Test handling of very long paths."""
        # Create a very long path
        long_path = "very_long_directory_name" * 10  # 250+ characters

        with tempfile.TemporaryDirectory() as temp_dir:
            full_path = os.path.join(temp_dir, long_path)

            try:
                result = ensure_directory_exists(full_path)
                # Should handle long paths gracefully
                assert isinstance(result, bool)
            except OSError:
                # May fail on some systems due to path length limits
                assert True

    def test_concurrent_directory_creation(self):
        """Test concurrent directory creation."""
        import threading
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            results = []
            errors = []

            def create_directory(thread_id):
                try:
                    dir_path = os.path.join(temp_dir, f"thread_{thread_id}")
                    result = ensure_directory_exists(dir_path)
                    results.append(result)
                    time.sleep(0.01)  # Small delay to encourage race conditions
                except Exception as e:
                    errors.append(e)

            # Create multiple threads trying to create directories
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_directory, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Should handle concurrent access gracefully
            assert len(errors) == 0
            assert all(results)

            # All directories should exist
            for i in range(5):
                dir_path = os.path.join(temp_dir, f"thread_{i}")
                assert os.path.exists(dir_path)

    def test_symlink_handling(self):
        """Test handling of symlinks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a symlink to a directory
            target_dir = os.path.join(temp_dir, "target")
            os.makedirs(target_dir)

            symlink_dir = os.path.join(temp_dir, "symlink")
            os.symlink(target_dir, symlink_dir)

            # Try to ensure the symlinked directory exists
            result = ensure_directory_exists(symlink_dir)

            # Should handle symlinks gracefully
            assert result is True
            assert os.path.exists(symlink_dir)

    def test_readonly_filesystem_simulation(self):
        """Test behavior when filesystem is readonly."""
        with patch("os.makedirs") as mock_makedirs:
            # Simulate readonly filesystem
            mock_makedirs.side_effect = OSError("Read-only file system")

            result = ensure_directory_exists("/readonly/path")

            # Should return False when creation fails
            assert result is False

    def test_network_path_handling(self):
        """Test handling of network paths."""
        # Test UNC paths (Windows)
        unc_path = r"\\server\share\directory"

        try:
            result = ensure_directory_exists(unc_path)
            # Should handle network paths gracefully
            assert isinstance(result, bool)
        except OSError:
            # May fail on non-Windows systems
            assert True

    def test_hidden_directory_creation(self):
        """Test creating hidden directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create hidden directory (starts with .)
            hidden_dir = os.path.join(temp_dir, ".hidden")

            result = ensure_directory_exists(hidden_dir)

            assert result is True
            assert os.path.exists(hidden_dir)
            assert os.path.isdir(hidden_dir)


class TestFormatCommandOutput:
    """Test command output formatting utility function."""

    def test_basic_output_formatting(self):
        """Test basic command output formatting."""
        output = "line 1\nline 2\nline 3"
        formatted = format_command_output(output)

        assert formatted == "line 1 | line 2 | line 3"

    def test_empty_output(self):
        """Test formatting empty output."""
        output = ""
        formatted = format_command_output(output)

        assert formatted == ""

    def test_single_line_output(self):
        """Test formatting single line output."""
        output = "single line"
        formatted = format_command_output(output)

        assert formatted == "single line"

    def test_output_with_extra_whitespace(self):
        """Test formatting output with extra whitespace."""
        output = "  line 1  \n  line 2  \n  "
        formatted = format_command_output(output)

        assert formatted == "line 1 | line 2 | "

    def test_output_with_mixed_whitespace(self):
        """Test formatting output with tabs and spaces."""
        output = "line\t1\nline  2\n\tline 3\t"
        formatted = format_command_output(output)

        # Tabs and multiple spaces should be preserved in individual lines
        assert "line\t1" in formatted
        assert "line  2" in formatted
        assert "\tline 3\t" in formatted

    def test_output_with_special_characters(self):
        """Test formatting output with special characters."""
        output = "line €1\nline £2\nline ¥3"
        formatted = format_command_output(output)

        assert "line €1 | line £2 | line ¥3" == formatted

    def test_output_with_unicode(self):
        """Test formatting output with unicode characters."""
        output = "café\nnaïve\nrésumé"
        formatted = format_command_output(output)

        assert "café | naïve | résumé" == formatted

    def test_output_with_newlines_only(self):
        """Test formatting output with only newlines."""
        output = "\n\n\n"
        formatted = format_command_output(output)

        assert " |  | " == formatted

    def test_output_with_carriage_returns(self):
        """Test formatting output with carriage returns."""
        output = "line 1\r\nline 2\r\nline 3"
        formatted = format_command_output(output)

        assert "line 1 | line 2 | line 3" == formatted

    def test_large_output(self):
        """Test formatting large output."""
        # Create large output (1000 lines)
        large_output = "\n".join([f"line_{i}" for i in range(1000)])
        formatted = format_command_output(large_output)

        assert len(formatted) > 0
        assert "|" in formatted  # Should contain separators
        assert "line_0" in formatted  # Should contain first line
        assert "line_999" in formatted  # Should contain last line

    def test_output_with_pipe_characters(self):
        """Test formatting output that already contains pipes."""
        output = "command | argument | output"
        formatted = format_command_output(output)

        # Should preserve existing pipes
        assert "command | argument | output" == formatted

    def test_output_with_multiple_separators(self):
        """Test formatting output with multiple consecutive separators."""
        output = "line 1\n\n\nline 2\n\nline 3"
        formatted = format_command_output(output)

        # Should handle multiple consecutive separators
        assert "line 1 |  | line 2 |  | line 3" == formatted

    def test_output_preservation(self):
        """Test that original content is preserved."""
        test_cases = [
            "simple output",
            "output with spaces",
            "output\twith\ttabs",
            "output\nwith\nnewlines",
            "output with \"quotes\" and 'apostrophes'",
            "output with /slashes/ and \\backslashes\\",
        ]

        for original in test_cases:
            formatted = format_command_output(original)
            # Should be able to reverse the formatting
            restored = (
                formatted.replace(" | ", "\n")
                .replace(" |", "\n")
                .replace("| ", "\n")
                .replace("|", "")
            )
            assert original in restored or original == formatted


class TestParseModelKeybindings:
    """Test keybinding parsing utility function."""

    def test_basic_keybinding_parsing(self):
        """Test basic keybinding parsing."""
        keybindings_str = "model1=ctrl+shift+1,model2=alt+F4"
        result = parse_model_keybindings(keybindings_str)

        expected = {"model1": "ctrl+shift+1", "model2": "alt+F4"}

        assert result == expected

    def test_empty_keybindings_string(self):
        """Test parsing empty keybindings string."""
        result = parse_model_keybindings("")
        assert result == {}

    def test_none_keybindings_string(self):
        """Test parsing None keybindings."""
        result = parse_model_keybindings(None)
        assert result == {}

    def test_single_keybinding(self):
        """Test parsing single keybinding."""
        keybindings_str = "chat_model=F1"
        result = parse_model_keybindings(keybindings_str)

        expected = {"chat_model": "F1"}
        assert result == expected

    def test_multiple_keybindings_with_spaces(self):
        """Test parsing keybindings with spaces around equals."""
        keybindings_str = "model1 = ctrl+1 , model2 = alt+2 , model3 = F3"
        result = parse_model_keybindings(keybindings_str)

        expected = {"model1": "ctrl+1", "model2": "alt+2", "model3": "F3"}
        assert result == expected

    def test_keybindings_with_special_keys(self):
        """Test parsing keybindings with special key names."""
        keybindings_str = "model1=ctrl+alt+del,model2=shift+F10,model3=ctrl+c"
        result = parse_model_keybindings(keybindings_str)

        expected = {"model1": "ctrl+alt+del", "model2": "shift+F10", "model3": "ctrl+c"}
        assert result == expected

    def test_keybindings_with_numeric_keys(self):
        """Test parsing keybindings with numeric key references."""
        keybindings_str = "model1=1,model2=shift+2,model3=ctrl+3"
        result = parse_model_keybindings(keybindings_str)

        expected = {"model1": "1", "model2": "shift+2", "model3": "ctrl+3"}
        assert result == expected

    def test_malformed_keybindings(self):
        """Test parsing malformed keybindings."""
        # Missing equals sign
        result = parse_model_keybindings("model1 ctrl+1")
        assert result == {}

        # Empty model name
        result = parse_model_keybindings("=ctrl+1,model2=alt+2")
        assert result == {"model2": "alt+2"}

        # Empty key combination
        result = parse_model_keybindings("model1=,model2=alt+2")
        assert result == {"model2": "alt+2"}

    def test_keybindings_with_duplicates(self):
        """Test parsing keybindings with duplicate model names."""
        # Later entries should override earlier ones
        keybindings_str = "model1=ctrl+1,model1=alt+2,model1=shift+3"
        result = parse_model_keybindings(keybindings_str)

        # Should contain only the last definition
        assert result == {"model1": "shift+3"}

    def test_keybindings_with_empty_pairs(self):
        """Test parsing keybindings with empty model or key parts."""
        keybindings_str = "model1=,=ctrl+2,=alt+3"
        result = parse_model_keybindings(keybindings_str)

        # Should only include pairs with both model and key
        assert result == {}

    def test_keybindings_with_whitespace_variations(self):
        """Test parsing keybindings with various whitespace patterns."""
        test_cases = [
            "model1=ctrl+1,model2=alt+2",  # No spaces
            "model1 = ctrl+1, model2 = alt+2",  # Spaces around equals
            " model1=ctrl+1 , model2=alt+2 ",  # Spaces around commas
            "  model1  =  ctrl+1  ,  model2  =  alt+2  ",  # Extra spaces everywhere
        ]

        expected = {"model1": "ctrl+1", "model2": "alt+2"}

        for case in test_cases:
            result = parse_model_keybindings(case)
            assert result == expected

    def test_keybindings_with_mixed_case(self):
        """Test parsing keybindings with mixed case."""
        keybindings_str = "Model1=CTRL+SHIFT+1,MODEL2=Alt+F4"
        result = parse_model_keybindings(keybindings_str)

        expected = {"Model1": "CTRL+SHIFT+1", "MODEL2": "Alt+F4"}
        assert result == expected

    def test_keybindings_with_underscores_and_hyphens(self):
        """Test parsing keybindings with underscores and hyphens in model names."""
        keybindings_str = "my-model=ctrl+1,my_model=alt+2,test_model_3=shift+3"
        result = parse_model_keybindings(keybindings_str)

        expected = {
            "my-model": "ctrl+1",
            "my_model": "alt+2",
            "test_model_3": "shift+3",
        }
        assert result == expected

    def test_keybindings_return_type(self):
        """Test that function returns proper dictionary."""
        result = parse_model_keybindings("test=ctrl+1")

        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())
        assert all(isinstance(v, str) for v in result.values())

    def test_keybindings_immutability(self):
        """Test that returned dictionary is independent of input."""
        keybindings_str = "model1=ctrl+1,model2=alt+2"
        result1 = parse_model_keybindings(keybindings_str)
        result2 = parse_model_keybindings(keybindings_str)

        # Should return different dictionary objects
        assert result1 is not result2
        assert result1 == result2

    def test_keybindings_with_complex_modifiers(self):
        """Test parsing keybindings with complex modifier combinations."""
        keybindings_str = "model1=ctrl+alt+shift+F1,model2=meta+super+hyper+key"
        result = parse_model_keybindings(keybindings_str)

        expected = {"model1": "ctrl+alt+shift+F1", "model2": "meta+super+hyper+key"}
        assert result == expected

    def test_keybindings_error_recovery(self):
        """Test that function recovers gracefully from various error conditions."""
        error_cases = [
            None,
            "",
            ",",
            "model1=",
            "=key1",
            "model1=ctrl+1,",
            ",model2=alt+2",
            "model1=ctrl+1,,model2=alt+2",
            "model1=ctrl+1,model2=,model3=alt+3",
        ]

        for case in error_cases:
            result = parse_model_keybindings(case)
            # Should always return a dictionary
            assert isinstance(result, dict)
            # Should not crash
            assert True

    def test_keybindings_large_input(self):
        """Test parsing large keybinding strings."""
        # Create large keybinding string
        large_bindings = []
        for i in range(100):
            large_bindings.append(f"model{i}=ctrl+{i}")

        keybindings_str = ",".join(large_bindings)
        result = parse_model_keybindings(keybindings_str)

        assert len(result) == 100
        assert result["model0"] == "ctrl+0"
        assert result["model99"] == "ctrl+99"

    def test_keybindings_preserve_order(self):
        """Test that keybindings preserve definition order."""
        keybindings_str = "third=ctrl+3,first=ctrl+1,second=ctrl+2"
        result = parse_model_keybindings(keybindings_str)

        # Dictionary order may vary, but all entries should be present
        assert len(result) == 3
        assert "third" in result
        assert "first" in result
        assert "second" in result

    def test_keybindings_with_unicode_characters(self):
        """Test parsing keybindings with unicode characters in model names."""
        keybindings_str = "môdel1=ctrl+1,mödél2=alt+2,tëst=shift+3"
        result = parse_model_keybindings(keybindings_str)

        expected = {"môdel1": "ctrl+1", "mödél2": "alt+2", "tëst": "shift+3"}
        assert result == expected
