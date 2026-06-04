# MIT License
#
# Copyright (c) 2024 mhand

"""HTTP routes exposing the Dograh integration to CC's web/UI surfaces.

The endpoints here never expose the dograh API key or other secrets to
the client — they always proxy through the in-process DograhClient
which reads its credentials from environment variables.

Routes:
    GET /api/v1/dograh/status   — availability + dograh /health passthrough
    GET /api/v1/dograh/workflows — list of workflow {id, name, status}
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Only these keys from dograh's /health body are projected to clients.
# Everything else (internal diagnostics, hostnames, etc.) is dropped so we
# never leak unexpected dograh internals through CC's public API surface.
_HEALTH_ALLOWLIST = ("status", "version")


class DograhStatus(BaseModel):
    available: bool = Field(
        ..., description="True if dograh is configured AND reachable."
    )
    reason: str | None = Field(
        default=None,
        description="When available is false, why (env not set, network, etc.).",
    )
    health: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Allowlisted subset of dograh's /api/v1/health body when reachable "
            "(only 'status' and 'version' are exposed)."
        ),
    )


class DograhWorkflow(BaseModel):
    id: int
    name: str
    status: str | None = None


router = APIRouter()


@router.get("/api/v1/dograh/status", response_model=DograhStatus)
async def get_dograh_status() -> DograhStatus:
    """Probe whether the configured dograh stack is reachable.

    Returns ``available=False`` with a reason when DOGRAH_BASE_URL /
    DOGRAH_API_KEY are missing or the service is down. The CC web UI
    uses this to render a connectivity badge.
    """
    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
            DograhError,
        )
    except ImportError as e:
        return DograhStatus(available=False, reason=f"import failed: {e}")

    try:
        client = DograhClient()
    except DograhError as e:
        return DograhStatus(available=False, reason=str(e))

    try:
        payload = client.health()
    except Exception as e:
        # Log the detailed error (which may include the dograh URL/hostname)
        # server-side only; never surface it to the client.
        logger.warning("dograh /health probe failed: %s", e)
        return DograhStatus(available=False, reason="unreachable")
    finally:
        client.close()

    # Project only an allowlist of keys so unexpected dograh internals never
    # reach the client.
    projected = {
        key: payload[key]
        for key in _HEALTH_ALLOWLIST
        if isinstance(payload, dict) and key in payload
    }
    return DograhStatus(available=True, health=projected)


@router.get(
    "/api/v1/dograh/workflows",
    response_model=list[DograhWorkflow],
)
async def get_dograh_workflows() -> list[DograhWorkflow]:
    """Proxy list of workflows from dograh for the CC UI.

    Returns an empty list when dograh is unconfigured / unreachable so
    the UI can degrade gracefully without surfacing 500s on the
    dashboard.
    """
    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
            DograhError,
        )
    except ImportError:
        return []

    try:
        client = DograhClient()
    except DograhError:
        return []

    try:
        workflows = client.list_workflows()
    except Exception:
        return []
    finally:
        client.close()

    return [
        DograhWorkflow(
            id=int(wf["id"]),
            name=str(wf.get("name", "")),
            status=wf.get("status"),
        )
        for wf in workflows
        if "id" in wf
    ]
