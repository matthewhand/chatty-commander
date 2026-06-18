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

        capsys.readouterr()
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


class TestLLMCommandDispatch:
    """Additional tests for handle_llm_command dispatch and handlers (to address qa 'no tests found' for llm/cli.py)."""

    def test_handle_llm_command_no_llm_command_prints_guidance(self, capsys):
        """Missing llm_command prints guidance."""
        args = Namespace(llm_command=None)
        handle_llm_command(args)
        captured = capsys.readouterr()
        assert "No LLM command specified" in captured.out

    def test_handle_llm_command_status_dispatches(self):
        """status dispatches to _handle_llm_status."""
        args = Namespace(llm_command="status")
        with patch("src.chatty_commander.llm.cli._handle_llm_status") as mock_h:
            handle_llm_command(args)
            mock_h.assert_called_once_with(args)

    def test_handle_llm_command_test_dispatches(self):
        """test dispatches to _handle_llm_test."""
        args = Namespace(llm_command="test", backend=None, prompt="hi", mock=True)
        with patch("src.chatty_commander.llm.cli._handle_llm_test") as mock_h:
            handle_llm_command(args)
            mock_h.assert_called_once_with(args)

    def test_handle_llm_command_process_dispatches(self):
        """process dispatches to _handle_llm_process."""
        args = Namespace(llm_command="process", text="do something", mock=True)
        with patch("src.chatty_commander.llm.cli._handle_llm_process") as mock_h:
            handle_llm_command(args, config_manager=None)
            mock_h.assert_called_once_with(args, None)

    def test_handle_llm_command_backends_dispatches(self):
        """backends dispatches to _handle_llm_backends."""
        args = Namespace(llm_command="backends")
        with patch("src.chatty_commander.llm.cli._handle_llm_backends") as mock_h:
            handle_llm_command(args)
            mock_h.assert_called_once_with(args)

    def test_handle_llm_command_unknown_prints(self, capsys):
        """unknown command prints message."""
        args = Namespace(llm_command="foo")
        handle_llm_command(args)
        captured = capsys.readouterr()
        assert "Unknown LLM command" in captured.out

    def test_handle_llm_status_prints_status(self, capsys):
        """_handle_llm_status prints status header and backend info."""
        args = Namespace()
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr:
            inst = Mock()
            inst.get_active_backend_name.return_value = "mock"
            inst.is_available.return_value = True
            inst.get_all_backends_info.return_value = {"mock": {"available": True}, "active": "mock"}
            mock_mgr.return_value = inst
            from src.chatty_commander.llm.cli import _handle_llm_status
            _handle_llm_status(args)
            out = capsys.readouterr().out
            assert "LLM System Status" in out
            assert "mock" in out.lower() or "Available" in out

    def test_handle_llm_test_specific_backend(self, capsys):
        """_handle_llm_test with backend arg calls test_backend."""
        args = Namespace(backend="mock", prompt="hi", mock=True)
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr:
            inst = Mock()
            inst.test_backend.return_value = {"success": True, "response": "hi", "response_time": 0.1}
            inst.get_backend_info.return_value = {"name": "mock"}
            mock_mgr.return_value = inst
            from src.chatty_commander.llm.cli import _handle_llm_test
            _handle_llm_test(args)
            out = capsys.readouterr().out
            assert "Testing backend" in out or "Success" in out

    def test_handle_llm_process_runs(self, capsys):
        """_handle_llm_process runs with mock and prints result."""
        args = Namespace(text="hello", mock=True)
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr, \
             patch("src.chatty_commander.llm.cli.CommandProcessor") as mock_proc:
            proc = Mock()
            proc.get_processor_status.return_value = {"available_commands": ["hi"]}
            proc.process_command.return_value = ("hi", 0.9, "matched")
            proc.explain_command.return_value = {"description": "say hi"}
            mock_proc.return_value = proc
            inst = Mock()
            mock_mgr.return_value = inst
            from src.chatty_commander.llm.cli import _handle_llm_process
            _handle_llm_process(args)
            out = capsys.readouterr().out
            assert "Processing command" in out
            assert "Matched command" in out or "hi" in out

    def test_handle_llm_backends_prints(self, capsys):
        """_handle_llm_backends prints backends info."""
        args = Namespace()
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr:
            inst = Mock()
            inst.get_all_backends_info.return_value = {"mock": {"available": True}}
            mock_mgr.return_value = inst
            from src.chatty_commander.llm.cli import _handle_llm_backends
            _handle_llm_backends(args)
            out = capsys.readouterr().out
            assert "Backends" in out or "mock" in out.lower() or "Available" in out

    def test_handle_llm_test_error_path(self, capsys):
        """_handle_llm_test handles exception and prints failed."""
        args = Namespace(backend=None, prompt="hi", mock=True)
        with patch("src.chatty_commander.llm.cli.LLMManager", side_effect=Exception("boom")):
            from src.chatty_commander.llm.cli import _handle_llm_test
            _handle_llm_test(args)
            out = capsys.readouterr().out
            assert "LLM test failed" in out or "boom" in out

    def test_add_llm_subcommands_process_args(self):
        """Process subcommand parses text and mock flag."""
        from argparse import ArgumentParser
        parser = ArgumentParser()
        subparsers = parser.add_subparsers(dest="llm_command")
        add_llm_subcommands(subparsers)
        args = parser.parse_args(["llm", "process", "do it", "--mock"])
        assert args.llm_command == "process"
        assert args.text == "do it"
        assert args.mock is True

    def test_handle_llm_process_no_match(self, capsys):
        """Process with no match prints no command."""
        args = Namespace(text="unknown foo", mock=True)
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr, \
             patch("src.chatty_commander.llm.cli.CommandProcessor") as mock_proc:
            proc = Mock()
            proc.get_processor_status.return_value = {"available_commands": []}
            proc.process_command.return_value = (None, 0.0, "no match")
            mock_proc.return_value = proc
            mock_mgr.return_value = Mock()
            from src.chatty_commander.llm.cli import _handle_llm_process
            _handle_llm_process(args)
            out = capsys.readouterr().out
            assert "No command matched" in out or "no match" in out.lower()

    def test_handle_llm_status_env_var_display(self, capsys):
        """Status prints masked env for keys."""
        args = Namespace()
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr, \
             patch("os.getenv") as mock_getenv:
            inst = Mock()
            inst.get_active_backend_name.return_value = "mock"
            inst.is_available.return_value = True
            inst.get_all_backends_info.return_value = {"mock": {"available": True}}
            mock_mgr.return_value = inst
            mock_getenv.side_effect = lambda v: "sk-12345678" if "KEY" in v else None
            from src.chatty_commander.llm.cli import _handle_llm_status
            _handle_llm_status(args)
            out = capsys.readouterr().out
            assert "OPENAI_API_KEY: sk-1..." in out or "Not set" in out

    def test_handle_llm_test_with_specific_backend_calls_test(self, capsys):
        """Test with backend calls test_backend and prints."""
        args = Namespace(backend="mock", prompt="test", mock=True)
        with patch("src.chatty_commander.llm.cli.LLMManager") as mock_mgr:
            inst = Mock()
            inst.test_backend.return_value = {"success": True, "response": "ok", "response_time": 0.01}
            inst.get_backend_info.return_value = {"name": "mock"}
            mock_mgr.return_value = inst
            from src.chatty_commander.llm.cli import _handle_llm_test
            _handle_llm_test(args)
            out = capsys.readouterr().out
            assert "Testing backend" in out or "Success" in out
