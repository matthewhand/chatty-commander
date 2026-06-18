# MIT License
#
# Copyright (c) 2024 mhand

"""HTTP routes exposing the Dograh integration to CC's web/UI surfaces.

The endpoints here never expose the dograh API key or other secrets to
the client — they always proxy through the in-process DograhClient
which reads its credentials from environment variables.

Routes:
    GET /api/v1/dograh/status     — availability + filtered dograh /health info
    GET /api/v1/dograh/workflows  — list of workflow {id, name, status}
    GET /api/v1/dograh/call-state — current cached dograh call state (phase-0
                                    state bridge; read without a WS)
    POST /api/v1/dograh/call-state/track   — start the call-state poller for
                                    a {workflow_id, run_id} (503 if dograh
                                    unconfigured; idempotent / re-track
                                    replaces)
    POST /api/v1/dograh/call-state/untrack — stop the call-state poller
                                    (safe when not tracking)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Only these keys from dograh's /health body are exposed to clients; the
# rest of the payload may contain internal details (hostnames, config).
_HEALTH_ALLOWED_KEYS = ("status", "version")


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
            "Filtered /api/v1/health body from dograh when reachable "
            "(only 'status' and 'version' keys are exposed)."
        ),
    )


class DograhWorkflow(BaseModel):
    id: int
    name: str
    status: str | None = None


class DograhTrackRequest(BaseModel):
    """Body for POST /api/v1/dograh/call-state/track."""

    workflow_id: int = Field(..., description="dograh workflow id to track")
    run_id: int = Field(..., description="dograh workflow-run id to track")


class DograhTrackResponse(BaseModel):
    tracking: bool
    workflow_id: int | None = Field(default=None)
    run_id: int | None = Field(default=None)


class DograhCallStateResponse(BaseModel):
    """Current CC-owned dograh *call* state (phase-0 state bridge).

    This is intentionally distinct from CC's StateManager mode
    (idle/chatty/computer): ``state`` is one of
    ``ringing``/``in_call``/``ended``/``unknown`` and reflects a dograh
    workflow-run's lifecycle, not CC's mode.
    """

    state: str = Field(
        ..., description="ringing | in_call | ended | unknown"
    )
    workflow_id: int | None = Field(default=None)
    run_id: int | None = Field(default=None)


router = APIRouter()


@router.get(
    "/api/v1/dograh/call-state",
    response_model=DograhCallStateResponse,
)
async def get_dograh_call_state() -> DograhCallStateResponse:
    """Return the latest cached dograh call state.

    Reads the in-memory holder updated by the call-state poller. When no
    run is being tracked (the default), this is ``unknown`` with null
    ids — so the endpoint is always safe to call even when dograh is
    unconfigured. Lets the UI/tests read call state without a WebSocket.
    """
    from chatty_commander.integrations.dograh_call_state import (
        get_call_state_holder,
    )

    snapshot = get_call_state_holder().get()
    return DograhCallStateResponse(
        state=snapshot.state,
        workflow_id=snapshot.workflow_id,
        run_id=snapshot.run_id,
    )


def _assert_dograh_configured() -> None:
    """Raise 503 unless DOGRAH_BASE_URL/API_KEY are set.

    Reuses the same configuration check the status route relies on:
    constructing a DograhClient raises DograhError (DograhUnavailableError)
    when the env vars are missing. We immediately close the probe client —
    the poller builds its own client server-side once tracking starts.
    """
    try:
        from chatty_commander.integrations.dograh_client import (
            DograhClient,
            DograhError,
        )
    except ImportError as e:  # pragma: no cover - import guard
        raise HTTPException(
            status_code=503, detail=f"dograh integration unavailable: {e}"
        ) from e

    try:
        client = DograhClient()
    except DograhError as e:
        # Unconfigured (or otherwise unusable) — clear 503 so callers know
        # tracking can't start until dograh is configured.
        raise HTTPException(status_code=503, detail=str(e)) from e
    client.close()


def _get_poller_registry():
    from chatty_commander.integrations.dograh_call_state import (
        get_poller_registry,
    )

    registry = get_poller_registry()
    if not registry.is_registered():
        # No WebModeServer has registered the poller lifecycle (e.g. a bare
        # app). Tracking can't be driven, so surface a clear 503 rather than
        # silently doing nothing.
        raise HTTPException(
            status_code=503,
            detail="dograh call-state poller lifecycle is not available",
        )
    return registry


@router.post(
    "/api/v1/dograh/call-state/track",
    response_model=DograhTrackResponse,
)
async def track_dograh_call_state(
    body: DograhTrackRequest,
) -> DograhTrackResponse:
    """Begin tracking a dograh workflow-run's call state.

    Starts the (otherwise dormant) call-state poller for ``{workflow_id,
    run_id}``: the poller reflects mapped state into the in-memory holder
    and broadcasts ``dograh_call_state`` over /ws. Idempotent — re-tracking
    replaces any active poller so only the latest run is followed.

    Returns 503 (clear error) when dograh is not configured or when no
    server poller lifecycle is registered. Auth-gated like the other
    /api/v1/dograh routes (the router carries no per-route auth; gating is
    applied at the app/router level).
    """
    _assert_dograh_configured()
    registry = _get_poller_registry()
    await registry.start(body.workflow_id, body.run_id)
    return DograhTrackResponse(
        tracking=True, workflow_id=body.workflow_id, run_id=body.run_id
    )


@router.post(
    "/api/v1/dograh/call-state/untrack",
    response_model=DograhTrackResponse,
)
async def untrack_dograh_call_state() -> DograhTrackResponse:
    """Stop tracking the current dograh workflow-run's call state.

    Safe to call when nothing is being tracked (no-op). Does not require
    dograh to be configured — stopping a poller never touches the network.
    """
    registry = _get_poller_registry()
    await registry.stop()
    return DograhTrackResponse(tracking=False)


def compute_dograh_status() -> DograhStatus:
    """Probe whether the configured dograh stack is reachable.

    Pure, synchronous helper shared by the REST route (GET
    /api/v1/dograh/status) and the /ws ``dograh_status`` push so both
    surfaces report exactly the same payload shape. Returns
    ``available=False`` with a reason when DOGRAH_BASE_URL / DOGRAH_API_KEY
    are missing or the service is down — never raises, so callers can use
    it to degrade gracefully (no dograh configured → honest offline status).
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
    except Exception:
        # Full details (including the internal dograh URL carried by
        # DograhHTTPError) stay in server-side logs; clients only see a
        # generic reason so internal endpoints are never leaked.
        logger.exception("dograh health check failed")
        return DograhStatus(available=False, reason="unreachable")
    finally:
        client.close()

    health: dict[str, Any] | None = None
    if isinstance(payload, dict):
        health = {k: payload[k] for k in _HEALTH_ALLOWED_KEYS if k in payload}
    return DograhStatus(available=True, health=health)


@router.get("/api/v1/dograh/status", response_model=DograhStatus)
async def get_dograh_status() -> DograhStatus:
    """Probe whether the configured dograh stack is reachable.

    Returns ``available=False`` with a reason when DOGRAH_BASE_URL /
    DOGRAH_API_KEY are missing or the service is down. The CC web UI
    uses this for the initial render of its connectivity badge; live
    updates after connect arrive over /ws as ``dograh_status`` messages.
    """
    return compute_dograh_status()


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
