"""CLI subcommands for the Dograh integration.

Usage::

    chatty-commander dograh health
    chatty-commander dograh list [--status active|archived]
    chatty-commander dograh call WORKFLOW_ID PHONE_NUMBER
                                  [--telephony-config-id N]

Requires the dograh stack to be reachable and ``DOGRAH_BASE_URL`` /
``DOGRAH_API_KEY`` to be set. The CLI surface is intentionally thin —
it wraps :class:`DograhClient` and writes results to stdout for shell
consumption.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def register_dograh_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the ``dograh`` subcommand group to a top-level subparser."""
    parser = subparsers.add_parser("dograh", help="Dograh integration utilities")
    ops = parser.add_subparsers(dest="dograh_op", help="Dograh operation")

    ops.add_parser("health", help="GET /api/v1/health on the configured dograh")

    list_parser = ops.add_parser("list", help="List workflows in the org")
    list_parser.add_argument(
        "--status",
        choices=["active", "archived"],
        default=None,
        help="Filter by workflow status",
    )
    list_parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of a table"
    )

    call_parser = ops.add_parser(
        "call", help="Place a telephony call via initiate-call"
    )
    call_parser.add_argument("workflow_id", type=int)
    call_parser.add_argument("phone_number", type=str)
    call_parser.add_argument(
        "--telephony-config-id",
        type=int,
        default=None,
        help="Optional telephony_configuration_id override",
    )

    show_parser = ops.add_parser("show", help="Show a workflow by id")
    show_parser.add_argument("workflow_id", type=int)

    runs_parser = ops.add_parser(
        "runs", help="List runs for a workflow"
    )
    runs_parser.add_argument("workflow_id", type=int)
    runs_parser.add_argument("--page", type=int, default=1)
    runs_parser.add_argument("--limit", type=int, default=20)
    runs_parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of a table"
    )

    run_parser = ops.add_parser(
        "run-info", help="Show a single workflow run by id"
    )
    run_parser.add_argument("workflow_id", type=int)
    run_parser.add_argument("run_id", type=int)


def handle_dograh(args: argparse.Namespace) -> int:
    """Dispatch a parsed ``dograh`` subcommand. Returns a shell exit code."""
    op = getattr(args, "dograh_op", None)
    if op is None:
        print(
            "usage: chatty-commander dograh {health|list|call} ...", file=sys.stderr
        )
        return 2

    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
            DograhError,
        )
    except ImportError as e:  # pragma: no cover - integration package guaranteed present
        print(f"dograh integration unavailable: {e}", file=sys.stderr)
        return 1

    try:
        client = DograhClient()
    except DograhError as e:
        print(f"dograh not configured: {e}", file=sys.stderr)
        return 1

    try:
        if op == "health":
            return _do_health(client)
        if op == "list":
            return _do_list(client, status=args.status, as_json=args.json)
        if op == "call":
            return _do_call(
                client,
                workflow_id=args.workflow_id,
                phone_number=args.phone_number,
                telephony_configuration_id=args.telephony_config_id,
            )
        if op == "show":
            return _do_show(client, workflow_id=args.workflow_id)
        if op == "runs":
            return _do_runs(
                client,
                workflow_id=args.workflow_id,
                page=args.page,
                limit=args.limit,
                as_json=args.json,
            )
        if op == "run-info":
            return _do_run_info(
                client, workflow_id=args.workflow_id, run_id=args.run_id
            )
    except DograhError as e:
        print(f"dograh error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"request failed: {e}", file=sys.stderr)
        return 1
    finally:
        client.close()

    print(f"unknown dograh op: {op}", file=sys.stderr)
    return 2


def _do_health(client: Any) -> int:
    payload = client.health()
    print(json.dumps(payload, indent=2))
    return 0


def _do_list(client: Any, *, status: str | None, as_json: bool) -> int:
    workflows = client.list_workflows(status=status) if status else client.list_workflows()
    if as_json:
        print(json.dumps(workflows, indent=2, default=str))
        return 0
    if not workflows:
        print("(no workflows)")
        return 0
    width = max(len(str(wf.get("id", ""))) for wf in workflows)
    for wf in workflows:
        print(f"{str(wf.get('id', '')).rjust(width)}  {wf.get('name', '')}")
    return 0


def _do_call(
    client: Any,
    *,
    workflow_id: int,
    phone_number: str,
    telephony_configuration_id: int | None,
) -> int:
    result = client.initiate_call(
        workflow_id,
        phone_number=phone_number,
        telephony_configuration_id=telephony_configuration_id,
    )
    # Intentionally NOT wiring get_poller_registry().request_start here: the
    # CLI is a short-lived process with no running web server / event loop, so
    # the trigger would be a guaranteed no-op (nothing registered). Auto-start
    # only matters for long-lived flows (command_executor / advisor tool) where
    # a web server may have registered its loop.
    print(json.dumps(result, indent=2, default=str))
    return 0


def _do_show(client: Any, *, workflow_id: int) -> int:
    workflow = client.get_workflow(workflow_id)
    print(json.dumps(workflow, indent=2, default=str))
    return 0


def _do_runs(
    client: Any,
    *,
    workflow_id: int,
    page: int,
    limit: int,
    as_json: bool,
) -> int:
    payload = client.list_workflow_runs(workflow_id, page=page, limit=limit)
    runs = payload.get("runs", []) if isinstance(payload, dict) else payload
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
        return 0
    if not runs:
        print("(no runs)")
        return 0
    for run in runs:
        rid = run.get("id", "?")
        mode = run.get("mode", "?")
        completed = "done" if run.get("is_completed") else "....."
        print(f"{rid:>6}  {completed:<5}  {mode:<10}  {run.get('name', '')}")
    return 0


def _do_run_info(client: Any, *, workflow_id: int, run_id: int) -> int:
    run = client.get_workflow_run(workflow_id, run_id)
    print(json.dumps(run, indent=2, default=str))
    return 0
