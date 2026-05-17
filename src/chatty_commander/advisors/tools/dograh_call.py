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

try:
    from agents import FunctionTool

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def dograh_place_call_tool(workflow_id: int, phone_number: str) -> str:
    """Place an outbound dograh call. Returns a status string for the agent.

    Args:
        workflow_id: ID of the dograh telephony workflow to execute.
        phone_number: E.164 phone number to dial.

    Returns:
        A short human-readable status describing what happened.
    """
    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
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
    except Exception as e:
        logger.warning("dograh_place_call failed: %s", e)
        return f"dograh call failed: {e}"
    finally:
        client.close()

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
