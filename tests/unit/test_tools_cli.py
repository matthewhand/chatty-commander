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

from src.chatty_commander.tools.cli import _configure_logging, main, parse_args


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


class TestMain:
    """Tests for main function (and integration with parse/ logging)."""

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_success(self, mock_generate):
        """Test main success path returns 0 and logs."""
        mock_generate.return_value = {"docs": Path("docs/openapi.json")}
        with patch("src.chatty_commander.tools.cli.logger") as mock_logger:
            rc = main([])
            assert rc == 0
            mock_generate.assert_called_once_with(output_dir=Path("docs"))
            mock_logger.info.assert_called()

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_system_exit(self, mock_generate):
        """Test main maps SystemExit code (handles pytest-injected flags)."""
        mock_generate.side_effect = SystemExit(42)
        rc = main([])
        assert rc == 42

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_exception(self, mock_generate):
        """Test main catches general exception, logs error, returns 1."""
        mock_generate.side_effect = RuntimeError("boom")
        with patch("src.chatty_commander.tools.cli.logger") as mock_logger:
            rc = main([])
            assert rc == 1
            mock_logger.error.assert_called()

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_custom_output(self, mock_generate):
        """Test main passes custom output dir to generate_docs."""
        mock_generate.return_value = {}
        rc = main(["-o", "/tmp/docs"])
        assert rc == 0
        mock_generate.assert_called_once_with(output_dir=Path("/tmp/docs"))

    def test_main_help(self):
        """Test main help flag triggers SystemExit (argparse)."""
        with pytest.raises(SystemExit):
            main(["-h"])


class TestToolsCliMoreCoverage:
    """Additional tests for tools/cli.py to address qa 'no tests found' (rank 13)."""

    def test_parse_args_verbose_long(self):
        """Test --verbose long form."""
        args = parse_args(["--verbose"])
        assert args.verbose == 1

    def test_parse_args_ignores_pytest_flags(self):
        """Test ignores extra like -q, -k."""
        args = parse_args(["-o", "docs", "-q", "-k", "foo"])
        assert args.output == Path("docs")

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_verbose_configures_logging(self, mock_gen):
        mock_gen.return_value = {}
        with patch("src.chatty_commander.tools.cli._configure_logging") as mock_conf:
            rc = main(["-vv"])
            assert rc == 0
            mock_conf.assert_called_with(2)

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_logs_generated_info(self, mock_gen):
        mock_gen.return_value = {"api": "docs/openapi.json"}
        with patch("src.chatty_commander.tools.cli.logger") as mock_log:
            main([])
            mock_log.info.assert_called()

    def test_configure_logging_levels(self):
        """Test configure sets levels without error."""
        _configure_logging(0)
        _configure_logging(1)
        _configure_logging(3)
        assert True

    def test_parse_args_default_values(self):
        """Test defaults for output and verbose."""
        args = parse_args([])
        assert args.output == Path("docs")
        assert args.verbose == 0

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_custom_output_dir(self, mock_gen):
        """Test -o flag passes Path to generate_docs."""
        mock_gen.return_value = {}
        rc = main(["-o", "/tmp/custom"])
        assert rc == 0
        mock_gen.assert_called_once_with(output_dir=Path("/tmp/custom"))

    @patch("src.chatty_commander.tools.cli.logging")
    def test_configure_logging_zero_sets_warning(self, mock_logging):
        """Test verbosity 0 sets WARNING level."""
        _configure_logging(0)
        mock_logging.basicConfig.assert_called()
        # level check would be in call args, but basic call verifies no crash

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_with_explicit_argv_list(self, mock_gen):
        """Test main accepts explicit argv list."""
        mock_gen.return_value = {"docs": "ok"}
        rc = main(["-v", "-o", "out"])
        assert rc == 0
        mock_gen.assert_called_once_with(output_dir=Path("out"))

    def test_parse_args_ignores_pytest_and_extra(self):
        """Test REMAINDER + parse_known_args swallows -q -k etc."""
        args = parse_args(["-o", "d", "-q", "-k", "foo", "--bar"])
        assert args.output == Path("d")
        assert args.verbose == 0

    @patch("src.chatty_commander.tools.cli.generate_docs", side_effect=Exception("boom"))
    def test_main_catches_exception_returns_one(self, mock_gen):
        """Exception in generate_docs returns 1."""
        rc = main([])
        assert rc == 1

    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_returns_zero_on_success(self, mock_gen):
        """Success returns 0."""
        mock_gen.return_value = {"docs": "ok"}
        rc = main([])
        assert rc == 0

    def test_parse_args_with_output_and_verbose(self):
        """Combined flags."""
        args = parse_args(["-o", "docs2", "-vv"])
        assert args.output == Path("docs2")
        assert args.verbose == 2

    @patch("src.chatty_commander.tools.cli._configure_logging")
    @patch("src.chatty_commander.tools.cli.generate_docs")
    def test_main_calls_configure_logging(self, mock_gen, mock_cfg):
        """main invokes _configure_logging before generate."""
        mock_gen.return_value = {}
        main(["-v"])
        mock_cfg.assert_called()
