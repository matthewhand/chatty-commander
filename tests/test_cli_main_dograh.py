"""Tests for ``python -m chatty_commander.cli.main dograh ...`` routing.

The ``dograh`` subcommand group is registered on the main parser
(``create_parser``) and dispatched immediately after argument parsing,
before any logger/config/model-manager initialisation. These tests pin
that behavior so the hard-coded ``sys.argv`` short-circuit removed from
``main()`` does not silently regress into heavy init (model loading).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from chatty_commander.cli.main import create_parser, main


class TestCreateParserDograh:
    def test_dograh_subcommand_registered(self):
        parser = create_parser()
        args, unknown = parser.parse_known_args(["dograh", "health"])
        assert args.subcommand == "dograh"
        assert args.dograh_op == "health"
        assert unknown == []

    def test_dograh_list_flags_parse(self):
        parser = create_parser()
        args, _ = parser.parse_known_args(
            ["dograh", "list", "--status", "active", "--json"]
        )
        assert args.dograh_op == "list"
        assert args.status == "active"
        assert args.json is True

    def test_mode_flags_still_parse_without_subcommand(self):
        parser = create_parser()
        args, _ = parser.parse_known_args(["--web", "--port", "9000"])
        assert args.subcommand is None
        assert args.web is True
        assert args.port == 9000


class TestMainDograhDispatch:
    @patch("chatty_commander.cli.main.setup_logger")
    @patch("chatty_commander.cli.dograh_cli.handle_dograh", return_value=0)
    def test_dograh_dispatches_without_heavy_init(
        self, mock_handle, mock_setup_logger, monkeypatch
    ):
        monkeypatch.setattr(
            "sys.argv", ["chatty-commander", "dograh", "health"]
        )
        assert main() == 0

        mock_handle.assert_called_once()
        args = mock_handle.call_args.args[0]
        assert args.subcommand == "dograh"
        assert args.dograh_op == "health"
        # setup_logger is the first thing main() does after the dograh
        # dispatch point; it must never run for dograh subcommands (proxy
        # for "no model loading / state-manager init happened").
        mock_setup_logger.assert_not_called()

    @patch("chatty_commander.cli.main.setup_logger")
    @patch("chatty_commander.cli.dograh_cli.handle_dograh", return_value=1)
    def test_dograh_exit_code_propagates(
        self, mock_handle, mock_setup_logger, monkeypatch
    ):
        monkeypatch.setattr(
            "sys.argv", ["chatty-commander", "dograh", "health"]
        )
        assert main() == 1
        mock_setup_logger.assert_not_called()

    @patch("chatty_commander.cli.main.setup_logger")
    def test_dograh_without_op_returns_2(self, mock_setup_logger, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["chatty-commander", "dograh"])
        with patch(
            "chatty_commander.integrations.dograh_client.DograhClient"
        ) as mock_cls:
            mock_cls.return_value = MagicMock()
            assert main() == 2

        assert "usage:" in capsys.readouterr().err.lower()
        mock_setup_logger.assert_not_called()

    @patch("chatty_commander.cli.main.setup_logger")
    def test_dograh_unknown_op_returns_2_from_argparse(
        self, mock_setup_logger, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            "sys.argv", ["chatty-commander", "dograh", "frobnicate"]
        )
        # argparse rejects the invalid op choice; main() converts the
        # SystemExit into the usual exit code 2.
        assert main() == 2
        assert "invalid choice" in capsys.readouterr().err
        mock_setup_logger.assert_not_called()
