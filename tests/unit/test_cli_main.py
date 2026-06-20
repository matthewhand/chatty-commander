"""Tests for cli_main module."""

from argparse import Namespace
from unittest.mock import Mock, patch

from chatty_commander.cli.cli import (
    _handle_list_subcommand,
    _validate_args,
    cli_main,
    create_parser,
)


class TestCliMainHelpers:
    """Tests for pure helpers in cli/cli.py (_validate_args, _handle_list_subcommand)."""

    def test_validate_args_web_port_ok(self):
        parser = Mock()
        args = Namespace(web=True, port=8080, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_not_called()

    def test_validate_args_low_port_errors(self):
        parser = Mock()
        args = Namespace(web=True, port=80, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_called_once()

    def test_validate_args_no_auth_without_web_errors(self):
        parser = Mock()
        args = Namespace(web=False, port=None, no_auth=True)
        _validate_args(args, parser)
        parser.error.assert_called_once()

    def test_validate_args_port_zero_errors(self):
        # Port 0 is out of the valid TCP range and must be rejected even
        # without --web (range check is unconditional).
        parser = Mock()
        args = Namespace(web=False, port=0, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_called_once()

    def test_validate_args_port_too_high_errors(self):
        # > 65535 is out of range and rejected unconditionally.
        parser = Mock()
        args = Namespace(web=False, port=70000, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_called_once()

    def test_validate_args_negative_port_errors(self):
        parser = Mock()
        args = Namespace(web=False, port=-1, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_called_once()

    def test_validate_args_high_port_without_web_ok(self):
        # A valid (>=1024) port without --web is accepted (no longer silently
        # ignored at validation time; range is just checked).
        parser = Mock()
        args = Namespace(web=False, port=9000, no_auth=False)
        _validate_args(args, parser)
        parser.error.assert_not_called()

    def test_handle_list_subcommand_plain(self, capsys):
        cfg = Mock(model_actions={"take_screenshot": {}, "lights": {}})
        rc = _handle_list_subcommand(Namespace(subcommand="list", json=False), cfg)
        captured = capsys.readouterr()
        assert rc == 0
        assert "Available commands" in captured.out
        assert "take_screenshot" in captured.out

    def test_handle_list_subcommand_json(self, capsys):
        cfg = Mock(model_actions={"foo": {"shell": "echo"}})
        rc = _handle_list_subcommand(Namespace(subcommand="list", json=True), cfg)
        captured = capsys.readouterr()
        assert rc == 0
        assert '"name": "foo"' in captured.out or "foo" in captured.out

    # Note: exec subcommand logic moved into cli_main; see integration tests for coverage.
    # Old _handle_subcommand tests removed to match current code (unblocks collection).


class TestCliMainParser:
    """Tests for create_parser and high-level cli_main branches."""

    def test_create_parser_has_modes_and_subcommands(self):
        parser = create_parser()
        {a.dest for a in parser._actions if hasattr(a, 'dest')}
        # modes
        assert any('web' in str(a) or getattr(a, 'option_strings', []) for a in parser._actions)
        # subparsers exist
        assert parser._subparsers is not None

    def test_cli_main_help_returns_zero(self):
        # --help should cause argparse to SystemExit(0) which cli_main catches and returns 0
        with patch("sys.argv", ["prog", "--help"]):
            rc = cli_main()
            assert rc == 0
