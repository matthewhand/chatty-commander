# MIT License
#
# Copyright (c) 2024 mhand

"""Dograh telephony tool for the OpenAI Agents-based advisor.

Exposes a single function-tool that lets the LLM place an outbound phone
call via a configured dograh workflow. Returns a short status string the
model can react to. Errors are returned as strings (never raised) so the
agent loop can surface them gracefully.

Opt-in via config block::

    advisors:
      tools:
        dograh_call:
          enabled: true
"""

from __future__ import annotations

import logging
import re

try:
    from agents import FunctionTool

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# E.164: optional leading '+', a non-zero leading digit, then 6-14 more digits.
_E164_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


def dograh_place_call_tool(workflow_id: int, phone_number: str) -> str:
    """Place an outbound dograh call. Returns a status string for the agent.

    Args:
        workflow_id: ID of the dograh telephony workflow to execute.
        phone_number: E.164 phone number to dial.

    Returns:
        A short human-readable status describing what happened.
    """
    # Security: workflow_id and phone_number are LLM-supplied. Validate both
    # before contacting the telephony backend so a prompt-injected reply can't
    # dial arbitrary numbers or pass non-numeric workflow ids.
    try:
        workflow_id = int(workflow_id)
    except (TypeError, ValueError):
        logger.warning("dograh_place_call rejected non-numeric workflow_id")
        return "dograh call rejected: invalid workflow_id (must be an integer)"

    if not isinstance(phone_number, str) or not _E164_RE.match(phone_number.strip()):
        # Do not echo the raw value back verbatim; keep the message generic.
        logger.warning("dograh_place_call rejected invalid phone number")
        return (
            "dograh call rejected: invalid phone number "
            "(expected E.164, e.g. +15555550100)"
        )
    phone_number = phone_number.strip()

    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
            DograhHTTPError,
            DograhUnavailableError,
        )
    except ImportError as e:  # pragma: no cover - integration package present
        return f"dograh integration not importable: {e}"

    try:
        client = DograhClient()
    except DograhUnavailableError as e:
        return f"dograh not configured: {e}"

    try:
        result = client.initiate_call(workflow_id, phone_number=phone_number)
    except DograhHTTPError as e:
        # Log status/detail only — never the URL, which leaks internal
        # endpoints into logs that may be surfaced to clients.
        logger.warning(
            "dograh_place_call failed: status=%s detail=%s",
            e.status_code,
            e.detail,
        )
        return f"dograh call failed: {e}"
    except Exception as e:
        logger.warning("dograh_place_call failed: %s", e)
        return f"dograh call failed: {e}"
    finally:
        client.close()

    # Auto-start the call-state poller so the dashboard CallStateBadge lights
    # up without a manual /track. No-op unless a web server has registered its
    # event loop (e.g. pure advisor with no server); never raises or blocks.
    try:
        from chatty_commander.integrations.dograh_call_state import (
            extract_run_id,
            get_poller_registry,
        )

        extracted_run_id = extract_run_id(result if isinstance(result, dict) else {})
        if extracted_run_id is not None:
            get_poller_registry().request_start(workflow_id, extracted_run_id)
    except Exception as exc:  # noqa: BLE001 - never fail a successful call
        logger.debug("dograh call-state auto-start failed: %s", exc)

    run_id = result.get("workflow_run_id") or result.get("id")
    return f"Call queued via dograh: workflow_run_id={run_id}"


dograh_call_tool_instance = None
if AGENTS_AVAILABLE:
    dograh_call_tool_instance = FunctionTool(
        name="dograh_place_call",
        description=(
            "Place an outbound phone call via Dograh using a pre-configured "
            "telephony workflow. Use this when the user asks you to call a "
            "phone number on their behalf. Returns a short status describing "
            "whether the call was queued."
        ),
        params_json_schema={
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "integer",
                    "description": "ID of the dograh telephony workflow to run.",
                },
                "phone_number": {
                    "type": "string",
                    "description": "E.164 phone number to dial (e.g. +15555550100).",
                },
            },
            "required": ["workflow_id", "phone_number"],
        },
        on_invoke_tool=dograh_place_call_tool,  # type: ignore[arg-type]
    )
