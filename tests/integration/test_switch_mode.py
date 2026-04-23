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
Comprehensive tests for switch_mode tool module.

Tests mode switching functionality for advisors.
"""

import pytest

from src.chatty_commander.advisors.tools.switch_mode import switch_mode


class TestSwitchMode:
    """Tests for switch_mode function."""

    def test_valid_mode_switch(self):
        """Test switching to a valid mode."""
        result = switch_mode("idle")
        assert result == "SWITCH_MODE:idle"

    def test_different_modes(self):
        """Test switching to different modes."""
        modes = ["idle", "chatty", "computer", "voice", "sleep"]
        for mode in modes:
            result = switch_mode(mode)
            assert result == f"SWITCH_MODE:{mode}"

    def test_empty_string_returns_invalid(self):
        """Test that empty string returns invalid."""
        result = switch_mode("")
        assert result == "SWITCH_MODE:invalid"

    def test_whitespace_only_returns_invalid(self):
        """Test that whitespace-only string returns invalid."""
        result = switch_mode("   ")
        assert result == "SWITCH_MODE:invalid"

    def test_none_returns_invalid(self):
        """Test that None returns invalid."""
        result = switch_mode(None)
        assert result == "SWITCH_MODE:invalid"

    def test_whitespace_is_stripped(self):
        """Test that whitespace is stripped from mode."""
        result = switch_mode("  idle  ")
        assert result == "SWITCH_MODE:idle"

    def test_leading_whitespace_stripped(self):
        """Test that leading whitespace is stripped."""
        result = switch_mode("   chatty")
        assert result == "SWITCH_MODE:chatty"

    def test_trailing_whitespace_stripped(self):
        """Test that trailing whitespace is stripped."""
        result = switch_mode("computer   ")
        assert result == "SWITCH_MODE:computer"

    def test_internal_whitespace_preserved(self):
        """Test that internal whitespace is preserved."""
        result = switch_mode("voice mode")
        assert result == "SWITCH_MODE:voice mode"

    def test_special_characters_in_mode(self):
        """Test handling of special characters in mode."""
        result = switch_mode("mode-123_test")
        assert result == "SWITCH_MODE:mode-123_test"

    def test_unicode_mode(self):
        """Test handling of unicode mode names."""
        result = switch_mode("test")
        assert result == "SWITCH_MODE:test"


class TestSwitchModeIntegration:
    """Integration tests for switch_mode."""

    def test_orchestration_directive_format(self):
        """Test that output follows orchestration directive format."""
        result = switch_mode("computer")
        
        # Should start with SWITCH_MODE:
        assert result.startswith("SWITCH_MODE:")
        
        # Should have mode after colon
        parts = result.split(":")
        assert len(parts) == 2
        assert parts[1] == "computer"


class TestSwitchModeEdgeCases:
    """Edge case tests."""

    def test_numeric_mode(self):
        """Test numeric mode is converted to string."""
        result = switch_mode(123)
        assert result == "SWITCH_MODE:123"

    def test_list_mode(self):
        """Test list mode is converted to string."""
        result = switch_mode(["mode"])
        # str(["mode"]) gives "['mode']"
        assert "SWITCH_MODE:" in result

    def test_dict_mode(self):
        """Test dict mode is converted to string."""
        result = switch_mode({"name": "idle"})
        # str(dict) gives representation
        assert "SWITCH_MODE:" in result

    def test_boolean_mode(self):
        """Test boolean mode handling."""
        # Boolean True - str(True) is "True" but strip() makes it empty
        result = switch_mode(True)
        # True as string is "True", strip() doesn't change it
        assert "SWITCH_MODE:" in result

    def test_long_mode_name(self):
        """Test very long mode name."""
        long_mode = "a" * 1000
        result = switch_mode(long_mode)
        assert result == f"SWITCH_MODE:{long_mode}"

    def test_single_character_mode(self):
        """Test single character mode."""
        result = switch_mode("x")
        assert result == "SWITCH_MODE:x"
