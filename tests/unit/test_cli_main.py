"""Tests for cli_main module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from chatty_commander.cli.cli import (
    cli_main,
    create_parser,
    _validate_args,
    _handle_subcommand,
)


class TestCliMainHelpers:
    """Tests for pure helpers in cli/cli.py (_validate_args, _handle_subcommand)."""

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

    def test_handle_subcommand_list_plain(self, capsys):
        cfg = Mock(model_actions={"take_screenshot": {}, "lights": {}})
        rc = _handle_subcommand(Namespace(subcommand="list", json=False), cfg, None, None, None, None)
        captured = capsys.readouterr()
        assert rc == 0
        assert "Available commands" in captured.out
        assert "take_screenshot" in captured.out

    def test_handle_subcommand_list_json(self, capsys):
        cfg = Mock(model_actions={"foo": {"shell": "echo"}})
        rc = _handle_subcommand(Namespace(subcommand="list", json=True), cfg, None, None, None, None)
        captured = capsys.readouterr()
        assert rc == 0
        assert '"name": "foo"' in captured.out or "foo" in captured.out

    def test_handle_subcommand_exec_dry_run(self, capsys):
        cfg = Mock(model_actions={"hi": {}})
        exe = Mock()
        rc = _handle_subcommand(Namespace(subcommand="exec", command_name="hi", dry_run=True), cfg, None, None, exe, None)
        assert rc == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        exe.execute_command.assert_not_called()

    def test_handle_subcommand_exec_unknown(self, capsys):
        cfg = Mock(model_actions={})
        with pytest.raises(SystemExit):
            _handle_subcommand(Namespace(subcommand="exec", command_name="nope", dry_run=False), cfg, None, None, Mock(), None)


class TestCliMainParser:
    """Tests for create_parser and high-level cli_main branches."""

    def test_create_parser_has_modes_and_subcommands(self):
        parser = create_parser()
        actions = {a.dest for a in parser._actions if hasattr(a, 'dest')}
        # modes
        assert any('web' in str(a) or getattr(a, 'option_strings', []) for a in parser._actions)
        # subparsers exist
        assert parser._subparsers is not None

    def test_cli_main_help_returns_zero(self):
        # --help should cause argparse to SystemExit(0) which cli_main catches and returns 0
        with patch("sys.argv", ["prog", "--help"]):
            rc = cli_main()
            assert rc == 0
