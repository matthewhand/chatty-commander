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
Tests for LLM CLI module.

Tests LLM-related CLI commands and handlers.
"""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.llm.cli import (
    add_llm_subcommands,
    handle_llm_command,
)


class TestAddLlmSubcommands:
    """Tests for add_llm_subcommands function."""

    @pytest.fixture
    def parser(self):
        """Create ArgumentParser with subparsers."""
        parser = ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        return parser, subparsers

    def test_adds_llm_command(self, parser):
        """Test that llm command is added."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        # Should create llm subcommand

    def test_llm_command_has_subcommands(self, parser):
        """Test that llm command has subcommands."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        # Parse to verify structure
        args = parser[0].parse_args(["llm", "status"])
        assert args.llm_command == "status"

    def test_status_subcommand(self, parser):
        """Test status subcommand."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args(["llm", "status"])
        assert args.llm_command == "status"

    def test_test_subcommand(self, parser):
        """Test test subcommand."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args(["llm", "test"])
        assert args.llm_command == "test"

    def test_test_subcommand_with_args(self, parser):
        """Test test subcommand with arguments."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args([
            "llm", "test",
            "--backend", "openai",
            "--prompt", "Hello",
            "--mock"
        ])
        assert args.llm_command == "test"
        assert args.backend == "openai"
        assert args.prompt == "Hello"
        assert args.mock is True

    def test_process_subcommand(self, parser):
        """Test process subcommand."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args(["llm", "process", "turn on lights"])
        assert args.llm_command == "process"
        assert args.text == "turn on lights"

    def test_process_subcommand_with_mock(self, parser):
        """Test process subcommand with mock flag."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args(["llm", "process", "hello", "--mock"])
        assert args.mock is True

    def test_backends_subcommand(self, parser):
        """Test backends subcommand."""
        _, subparsers = parser
        add_llm_subcommands(subparsers)
        
        args = parser[0].parse_args(["llm", "backends"])
        assert args.llm_command == "backends"


class TestHandleLlmCommand:
    """Tests for handle_llm_command function."""

    def test_no_command_prints_help(self, capsys):
        """Test handling when no command specified."""
        args = Namespace()
        
        handle_llm_command(args)
        
        captured = capsys.readouterr()
        assert "No LLM command specified" in captured.out

    def test_status_command(self):
        """Test handling status command."""
        args = Namespace(llm_command="status")
        
        with patch("src.chatty_commander.llm.cli._handle_llm_status") as mock_handler:
            handle_llm_command(args)
            mock_handler.assert_called_once()

    def test_test_command(self):
        """Test handling test command."""
        args = Namespace(llm_command="test", backend=None, prompt="Hello", mock=False)
        
        with patch("src.chatty_commander.llm.cli._handle_llm_test") as mock_handler:
            handle_llm_command(args)
            mock_handler.assert_called_once_with(args)

    def test_process_command(self):
        """Test handling process command."""
        args = Namespace(llm_command="process", text="hello", mock=False)
        
        with patch("src.chatty_commander.llm.cli._handle_llm_process") as mock_handler:
            handle_llm_command(args)
            mock_handler.assert_called_once_with(args, None)

    def test_backends_command(self):
        """Test handling backends command."""
        args = Namespace(llm_command="backends")
        
        with patch("src.chatty_commander.llm.cli._handle_llm_backends") as mock_handler:
            handle_llm_command(args)
            mock_handler.assert_called_once()

    def test_unknown_command(self, capsys):
        """Test handling unknown command."""
        args = Namespace(llm_command="unknown")
        
        handle_llm_command(args)
        
        captured = capsys.readouterr()
        assert "Unknown LLM command" in captured.out


class TestHandleLlmStatus:
    """Tests for _handle_llm_status function."""

    def test_status_output(self, capsys):
        """Test status command produces output."""
        from src.chatty_commander.llm.cli import _handle_llm_status
        
        args = Namespace()
        _handle_llm_status(args)
        
        captured = capsys.readouterr()
        assert "LLM System Status" in captured.out

    def test_shows_dependencies(self, capsys):
        """Test status shows dependencies."""
        from src.chatty_commander.llm.cli import _handle_llm_status
        
        args = Namespace()
        _handle_llm_status(args)
        
        captured = capsys.readouterr()
        assert "Dependencies" in captured.out or "LLM Manager" in captured.out


class TestHandleLlmTest:
    """Tests for _handle_llm_test function."""

    def test_test_output(self, capsys):
        """Test test command produces output."""
        from src.chatty_commander.llm.cli import _handle_llm_test
        
        args = Namespace(backend=None, prompt="Hello", mock=True)
        _handle_llm_test(args)
        
        captured = capsys.readouterr()
        assert "Testing" in captured.out or "LLM" in captured.out


class TestHandleLlmProcess:
    """Tests for _handle_llm_process function."""

    def test_process_output(self, capsys):
        """Test process command produces output."""
        from src.chatty_commander.llm.cli import _handle_llm_process
        
        args = Namespace(text="hello", mock=True)
        _handle_llm_process(args)
        
        captured = capsys.readouterr()
        # Should produce some output


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_text_process(self):
        """Test process with empty text."""
        from src.chatty_commander.llm.cli import _handle_llm_process
        
        args = Namespace(text="", mock=True)
        # Should not crash
        _handle_llm_process(args)

    def test_long_text_process(self):
        """Test process with very long text."""
        from src.chatty_commander.llm.cli import _handle_llm_process
        
        long_text = "hello " * 1000
        args = Namespace(text=long_text, mock=True)
        # Should handle long text
        _handle_llm_process(args)
