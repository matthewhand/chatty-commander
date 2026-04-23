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

"""Tests for tools CLI module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.chatty_commander.tools.cli import _configure_logging, parse_args


class TestParseArgs:
    """Tests for parse_args function."""

    def test_default_args(self):
        """Test parsing with default arguments."""
        args = parse_args([])
        assert args.output == Path("docs")
        assert args.verbose == 0

    def test_custom_output(self):
        """Test parsing custom output directory."""
        args = parse_args(["-o", "/custom/path"])
        assert args.output == Path("/custom/path")

    def test_verbose_flag(self):
        """Test parsing verbose flag."""
        args = parse_args(["-v"])
        assert args.verbose == 1

    def test_verbose_multiple(self):
        """Test parsing multiple verbose flags."""
        args = parse_args(["-vv"])
        assert args.verbose == 2

    def test_verbose_long_form(self):
        """Test parsing verbose long form."""
        args = parse_args(["--verbose"])
        assert args.verbose == 1

    def test_combined_args(self):
        """Test parsing combined arguments."""
        args = parse_args(["-o", "/output", "-vv"])
        assert args.output == Path("/output")
        assert args.verbose == 2

    def test_ignores_extra_args(self):
        """Test that extra arguments are ignored."""
        args = parse_args(["-o", "/output", "--", "extra", "args"])
        assert args.output == Path("/output")

    def test_help_flag(self):
        """Test that help flag exits."""
        with pytest.raises(SystemExit):
            parse_args(["-h"])


class TestConfigureLogging:
    """Tests for _configure_logging function."""

    def test_default_verbosity(self):
        """Test default verbosity level."""
        # Should not raise
        _configure_logging(0)

    def test_info_verbosity(self):
        """Test info verbosity level."""
        # Should not raise
        _configure_logging(1)

    def test_debug_verbosity(self):
        """Test debug verbosity level."""
        # Should not raise
        _configure_logging(2)

    def test_high_verbosity(self):
        """Test very high verbosity."""
        # Should not raise
        _configure_logging(10)
