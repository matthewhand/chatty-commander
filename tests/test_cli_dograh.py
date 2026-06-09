"""Tests for the ``chatty-commander dograh`` CLI subcommand group."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

from chatty_commander.cli.dograh_cli import (
    handle_dograh,
    register_dograh_subparser,
)
from chatty_commander.integrations.dograh_client import (
    DograhError,
    DograhUnavailableError,
)


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="subcommand")
    register_dograh_subparser(subs)
    return parser.parse_args(argv)


class TestDograhSubparser:
    def test_health_parses(self):
        args = _parse(["dograh", "health"])
        assert args.subcommand == "dograh"
        assert args.dograh_op == "health"

    def test_list_parses_with_status_and_json(self):
        args = _parse(["dograh", "list", "--status", "active", "--json"])
        assert args.dograh_op == "list"
        assert args.status == "active"
        assert args.json is True

    def test_call_parses_required_args(self):
        args = _parse(["dograh", "call", "42", "+15555550100"])
        assert args.dograh_op == "call"
        assert args.workflow_id == 42
        assert args.phone_number == "+15555550100"
        assert args.telephony_config_id is None


class TestHandleDograh:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_health_prints_payload(self, mock_cls, capsys):
        instance = MagicMock()
        instance.health.return_value = {"status": "ok", "version": "1.30.0"}
        mock_cls.return_value = instance

        args = _parse(["dograh", "health"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        assert '"status": "ok"' in out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_list_table_output(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflows.return_value = [
            {"id": 1, "name": "first"},
            {"id": 22, "name": "second"},
        ]
        mock_cls.return_value = instance

        args = _parse(["dograh", "list"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        assert "first" in out
        assert "second" in out
        # Right-aligned ids with the wider value setting the column.
        assert " 1  first" in out
        assert "22  second" in out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_list_empty_message(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflows.return_value = []
        mock_cls.return_value = instance

        args = _parse(["dograh", "list"])
        assert handle_dograh(args) == 0
        assert "(no workflows)" in capsys.readouterr().out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_list_passes_status_filter(self, mock_cls):
        instance = MagicMock()
        instance.list_workflows.return_value = []
        mock_cls.return_value = instance

        args = _parse(["dograh", "list", "--status", "archived"])
        handle_dograh(args)

        instance.list_workflows.assert_called_once_with(status="archived")

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_call_invokes_initiate_call(self, mock_cls, capsys):
        instance = MagicMock()
        instance.initiate_call.return_value = {"workflow_run_id": 9}
        mock_cls.return_value = instance

        args = _parse(["dograh", "call", "42", "+15555550100"])
        assert handle_dograh(args) == 0

        instance.initiate_call.assert_called_once_with(
            42, phone_number="+15555550100", telephony_configuration_id=None
        )
        assert "workflow_run_id" in capsys.readouterr().out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_show_prints_workflow(self, mock_cls, capsys):
        instance = MagicMock()
        instance.get_workflow.return_value = {"id": 7, "name": "demo"}
        mock_cls.return_value = instance

        args = _parse(["dograh", "show", "7"])
        assert handle_dograh(args) == 0

        instance.get_workflow.assert_called_once_with(7)
        assert '"id": 7' in capsys.readouterr().out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_runs_table(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflow_runs.return_value = {
            "runs": [
                {"id": 1, "mode": "chat", "is_completed": True, "name": "r1"},
                {"id": 2, "mode": "twilio", "is_completed": False, "name": "r2"},
            ]
        }
        mock_cls.return_value = instance

        args = _parse(["dograh", "runs", "5"])
        assert handle_dograh(args) == 0

        instance.list_workflow_runs.assert_called_once_with(5, page=1, limit=20)
        out = capsys.readouterr().out
        assert "done" in out
        assert "....." in out
        assert "r1" in out and "r2" in out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_runs_empty(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflow_runs.return_value = {"runs": []}
        mock_cls.return_value = instance

        args = _parse(["dograh", "runs", "5"])
        assert handle_dograh(args) == 0
        assert "(no runs)" in capsys.readouterr().out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_run_info_prints_full_run(self, mock_cls, capsys):
        instance = MagicMock()
        instance.get_workflow_run.return_value = {"id": 9, "recording_url": "s3://x"}
        mock_cls.return_value = instance

        args = _parse(["dograh", "run-info", "5", "9"])
        assert handle_dograh(args) == 0

        instance.get_workflow_run.assert_called_once_with(5, 9)
        assert '"recording_url": "s3://x"' in capsys.readouterr().out

    def test_missing_op_returns_usage(self, capsys):
        args = _parse(["dograh"])
        assert handle_dograh(args) == 2
        assert "usage:" in capsys.readouterr().err.lower()

    @patch(
        "chatty_commander.integrations.dograh_client.DograhConfig.from_env",
        side_effect=DograhUnavailableError("DOGRAH_BASE_URL not set"),
    )
    def test_unconfigured_dograh_returns_1(self, _mock, capsys, monkeypatch):
        # Belt-and-braces: ensure env is actually clean too.
        monkeypatch.delenv("DOGRAH_BASE_URL", raising=False)
        monkeypatch.delenv("DOGRAH_API_KEY", raising=False)

        args = _parse(["dograh", "health"])
        assert handle_dograh(args) == 1
        assert "not configured" in capsys.readouterr().err.lower()


class TestHandleDograhErrorBranches:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_dograh_error_in_dispatch_returns_1(self, mock_cls, capsys):
        instance = MagicMock()
        instance.health.side_effect = DograhError("backend exploded")
        mock_cls.return_value = instance

        args = _parse(["dograh", "health"])
        assert handle_dograh(args) == 1

        err = capsys.readouterr().err
        assert "dograh error: backend exploded" in err
        # Client is still closed on the error path.
        instance.close.assert_called_once_with()

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_generic_exception_in_dispatch_returns_1(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflows.side_effect = ValueError("totally unexpected")
        mock_cls.return_value = instance

        args = _parse(["dograh", "list"])
        assert handle_dograh(args) == 1

        err = capsys.readouterr().err
        assert "request failed: totally unexpected" in err
        instance.close.assert_called_once_with()

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_unknown_op_returns_2(self, mock_cls, capsys):
        # The parser rejects unknown ops, so build the namespace directly to
        # exercise the dispatcher's fall-through guard.
        mock_cls.return_value = MagicMock()

        args = argparse.Namespace(subcommand="dograh", dograh_op="frobnicate")
        assert handle_dograh(args) == 2

        err = capsys.readouterr().err
        assert "unknown dograh op: frobnicate" in err


class TestHandleDograhJsonOutput:
    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_list_json_output(self, mock_cls, capsys):
        workflows = [
            {"id": 1, "name": "first"},
            {"id": 22, "name": "second"},
        ]
        instance = MagicMock()
        instance.list_workflows.return_value = workflows
        mock_cls.return_value = instance

        args = _parse(["dograh", "list", "--json"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        assert json.loads(out) == workflows

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_list_json_output_for_empty_list(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflows.return_value = []
        mock_cls.return_value = instance

        args = _parse(["dograh", "list", "--json"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        assert json.loads(out) == []
        assert "(no workflows)" not in out

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_runs_json_output_prints_full_payload(self, mock_cls, capsys):
        payload = {
            "runs": [
                {"id": 1, "mode": "chat", "is_completed": True, "name": "r1"},
            ],
            "total": 1,
        }
        instance = MagicMock()
        instance.list_workflow_runs.return_value = payload
        mock_cls.return_value = instance

        args = _parse(["dograh", "runs", "5", "--json"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        # The full payload (including pagination metadata) is emitted as JSON.
        assert json.loads(out) == payload

    @patch("chatty_commander.integrations.dograh_client.DograhClient")
    def test_runs_json_output_for_empty_runs(self, mock_cls, capsys):
        instance = MagicMock()
        instance.list_workflow_runs.return_value = {"runs": []}
        mock_cls.return_value = instance

        args = _parse(["dograh", "runs", "5", "--json"])
        assert handle_dograh(args) == 0

        out = capsys.readouterr().out
        assert json.loads(out) == {"runs": []}
        assert "(no runs)" not in out
