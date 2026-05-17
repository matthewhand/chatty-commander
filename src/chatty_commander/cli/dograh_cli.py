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
    print(json.dumps(result, indent=2, default=str))
    return 0
