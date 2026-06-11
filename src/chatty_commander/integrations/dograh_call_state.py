# MIT License
#
# Copyright (c) 2024 mhand

"""Phase-0 dograh call-state bridge (state-only, no shared audio).

This module reflects dograh *call* state into ChattyCommander so the
dashboard can show live call status. It is deliberately a **state-only**
bridge: no audio is shared, and no new dograh capability is assumed
beyond the REST surface that ``DograhClient`` already exposes.

Design notes (see docs/developer/WEBRTC_BRIDGE_SPIKE.md, "Phase 0"):

- We poll ``DograhClient.get_workflow_run(workflow_id, run_id)`` on an
  interval and map the run's state to a small, CC-owned set of *call*
  states (``ringing`` / ``in_call`` / ``ended`` / ``unknown``).
- These call states are kept **separate** from CC's ``StateManager``
  mode enum (``idle``/``chatty``/``computer``). The spike explicitly
  warns against conflating dograh call state with CC mode state, so we
  broadcast a dedicated ``dograh_call_state`` WS message and keep a small
  in-memory holder rather than mutating ``StateManager``.

UNVERIFIED ASSUMPTION (must be confirmed against a live dograh instance):

    The exact field name on a run record that encodes the call's
    lifecycle is **not known** without a live dograh. We assume it is
    one of ``_RUN_STATE_FIELDS`` (see below) and that its values map via
    ``_DOGRAH_STATE_TO_CALL_STATE``. Both are single, easy-to-correct
    constants. If a live instance uses a different field name or values,
    update those two constants only — the rest of the bridge is generic.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# --- CC-owned call states (intentionally NOT StateManager modes) ---------

CALL_STATE_RINGING = "ringing"
CALL_STATE_IN_CALL = "in_call"
CALL_STATE_ENDED = "ended"
CALL_STATE_UNKNOWN = "unknown"

# --- UNVERIFIED dograh run-record assumptions ----------------------------
#
# The run-state field name is unknown without a live dograh instance. We
# probe these candidate keys in order and use the first one present. This
# is the single place to correct once the real field is confirmed.
_RUN_STATE_FIELDS: tuple[str, ...] = ("state", "status", "call_status", "phase")

# Map of (lower-cased) dograh run-state value -> CC call state. Unknown /
# unmapped values fall through to CALL_STATE_UNKNOWN. Again: the value
# vocabulary here is a best-effort guess pending live confirmation.
_DOGRAH_STATE_TO_CALL_STATE: dict[str, str] = {
    # ringing / dialing / queued
    "ringing": CALL_STATE_RINGING,
    "dialing": CALL_STATE_RINGING,
    "queued": CALL_STATE_RINGING,
    "initiated": CALL_STATE_RINGING,
    "pending": CALL_STATE_RINGING,
    # active / answered / in progress
    "in_call": CALL_STATE_IN_CALL,
    "in-call": CALL_STATE_IN_CALL,
    "in_progress": CALL_STATE_IN_CALL,
    "in-progress": CALL_STATE_IN_CALL,
    "active": CALL_STATE_IN_CALL,
    "answered": CALL_STATE_IN_CALL,
    "running": CALL_STATE_IN_CALL,
    "connected": CALL_STATE_IN_CALL,
    # terminal
    "ended": CALL_STATE_ENDED,
    "completed": CALL_STATE_ENDED,
    "complete": CALL_STATE_ENDED,
    "finished": CALL_STATE_ENDED,
    "failed": CALL_STATE_ENDED,
    "canceled": CALL_STATE_ENDED,
    "cancelled": CALL_STATE_ENDED,
    "hung_up": CALL_STATE_ENDED,
    "hangup": CALL_STATE_ENDED,
}

# Terminal call states — once reached, the poller stops polling.
_TERMINAL_CALL_STATES = frozenset({CALL_STATE_ENDED})


def extract_run_state(run: dict[str, Any]) -> str | None:
    """Pull the raw dograh run-state string from a run record, if present.

    Returns the first non-empty value among ``_RUN_STATE_FIELDS`` or
    ``None`` if no candidate field is present. Kept separate from mapping
    so the field-name assumption is testable in isolation.
    """
    for field in _RUN_STATE_FIELDS:
        value = run.get(field)
        if value is not None and str(value).strip():
            return str(value)
    return None


def map_dograh_state(raw_state: str | None) -> str:
    """Map a raw dograh run-state value to a CC call state.

    Any unknown / missing value maps to ``CALL_STATE_UNKNOWN``.
    """
    if raw_state is None:
        return CALL_STATE_UNKNOWN
    return _DOGRAH_STATE_TO_CALL_STATE.get(
        raw_state.strip().lower(), CALL_STATE_UNKNOWN
    )


def map_run_record(run: dict[str, Any]) -> str:
    """Convenience: extract + map in one call from a run record."""
    return map_dograh_state(extract_run_state(run))


# --- UNVERIFIED initiate_call RESULT run-id assumptions ------------------
#
# The shape of the dict returned by ``DograhClient.initiate_call`` is not
# known without a live dograh instance. To auto-start the poller right after
# a call begins we must pull the *run id* out of that result. We probe these
# candidate locations in order and use the first that yields an int-coercible
# value. The workflow id is always known (it's the call arg), so only the run
# id needs extraction.
#
# This mirrors the _RUN_STATE_FIELDS pattern above: a single isolated place
# to correct once the real result shape is confirmed against a live dograh.
#   * top-level keys: workflow_run_id / run_id / id
#   * nested:         run.id
def extract_run_id(result: dict[str, Any]) -> int | None:
    """Pull the run id from an ``initiate_call`` result dict, if present.

    Returns the first int-coercible value among the assumed candidate
    locations, or ``None`` if none is present / coercible. Never raises.
    """
    if not isinstance(result, dict):
        return None
    candidates: list[Any] = [
        result.get("workflow_run_id"),
        result.get("run_id"),
        result.get("id"),
    ]
    run = result.get("run")
    if isinstance(run, dict):
        candidates.append(run.get("id"))
    for value in candidates:
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


class _RunFetcher(Protocol):
    """Structural type for the bit of DograhClient the poller needs."""

    def get_workflow_run(self, workflow_id: int, run_id: int) -> dict[str, Any]: ...


@dataclass
class DograhCallState:
    """Snapshot of the current dograh call state for one run."""

    state: str = CALL_STATE_UNKNOWN
    workflow_id: int | None = None
    run_id: int | None = None

    def as_message_data(self) -> dict[str, Any]:
        """Shape used as the ``data`` of a ``dograh_call_state`` WS message."""
        return {
            "state": self.state,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
        }


# Callback invoked on every *transition*. May be sync or async; the poller
# awaits it if it returns an awaitable.
OnChange = Callable[[DograhCallState], Awaitable[None] | None]

# Injectable async sleep so tests never block on real seconds.
SleepFn = Callable[[float], Awaitable[None]]


class DograhCallStatePoller:
    """Polls one dograh workflow-run's state and fires a callback on change.

    Pure / injectable: the dograh client, the change callback, the poll
    interval and the sleep function are all constructor args, so unit
    tests drive it with a fake client and a manual clock — no real sleeps,
    no live dograh instance.

    Lifecycle: ``start()`` launches a cancellable asyncio task; ``stop()``
    cancels and awaits it. The loop also self-terminates once a terminal
    call state (``ended``) is observed, so a finished call stops polling
    on its own.
    """

    def __init__(
        self,
        client: _RunFetcher,
        workflow_id: int,
        run_id: int,
        on_change: OnChange,
        *,
        interval_seconds: float = 2.0,
        sleep: SleepFn | None = None,
    ) -> None:
        self._client = client
        self._workflow_id = workflow_id
        self._run_id = run_id
        self._on_change = on_change
        self._interval = interval_seconds
        self._sleep: SleepFn = sleep or asyncio.sleep
        self._current = DograhCallState(
            state=CALL_STATE_UNKNOWN, workflow_id=workflow_id, run_id=run_id
        )
        self._task: asyncio.Task[None] | None = None

    @property
    def current(self) -> DograhCallState:
        """The most recently observed call state."""
        return self._current

    async def poll_once(self) -> bool:
        """Fetch the run once, update state, fire callback on transition.

        Returns ``True`` if the state changed (callback fired), else
        ``False``. Network/parse errors are swallowed (logged) and treated
        as "no change" so a transient dograh hiccup never crashes the loop.
        """
        try:
            run = self._client.get_workflow_run(self._workflow_id, self._run_id)
        except Exception as exc:  # noqa: BLE001 - resilience: never crash the poller
            logger.debug("dograh get_workflow_run failed: %s", exc)
            return False

        new_state = map_run_record(run if isinstance(run, dict) else {})
        if new_state == self._current.state:
            return False

        self._current = DograhCallState(
            state=new_state,
            workflow_id=self._workflow_id,
            run_id=self._run_id,
        )
        await self._fire(self._current)
        return True

    async def _fire(self, snapshot: DograhCallState) -> None:
        try:
            result = self._on_change(snapshot)
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:  # noqa: BLE001 - callback must not kill the poller
            logger.debug("dograh_call_state on_change callback failed: %s", exc)

    async def run(self) -> None:
        """Poll until a terminal state is reached or the task is cancelled."""
        try:
            while True:
                await self.poll_once()
                if self._current.state in _TERMINAL_CALL_STATES:
                    return
                await self._sleep(self._interval)
        except asyncio.CancelledError:
            raise

    def start(self) -> asyncio.Task[None]:
        """Launch the poll loop as a cancellable task (idempotent)."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self) -> None:
        """Cancel the poll loop and await its teardown."""
        task = self._task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None


# --- Process-wide current-call-state holder ------------------------------
#
# A tiny in-memory cache of the latest call state so the read route
# (GET /api/v1/dograh/call-state) can serve it without a WS, and so the
# poller and any future producers share one source of truth. This holds CC
# *call* state only — it never touches StateManager's mode enum.


class DograhCallStateHolder:
    """Thread-/task-light holder for the latest dograh call state.

    Intentionally trivial: a single mutable snapshot with a getter/setter.
    Wired but dormant by default — it only ever reflects a non-``unknown``
    state once a poller (registered for an active run) updates it.
    """

    def __init__(self) -> None:
        self._snapshot = DograhCallState()

    def get(self) -> DograhCallState:
        return self._snapshot

    def set(self, snapshot: DograhCallState) -> None:
        self._snapshot = snapshot


# Module-level singleton used by the route and the broadcast wiring.
_HOLDER = DograhCallStateHolder()


def get_call_state_holder() -> DograhCallStateHolder:
    """Return the process-wide call-state holder."""
    return _HOLDER


# --- Process-wide poller-lifecycle registry ------------------------------
#
# The poller's lifecycle (start/stop) lives on the WebModeServer instance,
# but the HTTP route handlers in web/routes/dograh.py are module-level
# functions with no clean reference to that instance. Mirroring the holder
# pattern above, web_mode registers small start/stop callables here at
# startup, and the track/untrack routes reach the poller through this
# registry. This keeps the route layer decoupled from WebModeServer while
# reusing the existing module-level-accessor convention.
#
# start callable: (workflow_id: int, run_id: int) -> None   (idempotent;
#   re-track replaces the active poller)
# stop callable:  () -> Awaitable[None] | None              (safe to call
#   when nothing is tracked)

StartPoller = Callable[[int, int], Awaitable[None] | None]
StopPoller = Callable[[], Awaitable[None] | None]


class DograhPollerRegistry:
    """Holds the process-wide start/stop callables for the call-state poller.

    Registered by WebModeServer at startup; consumed by the track/untrack
    routes. When nothing is registered (e.g. a bare app without a running
    WebModeServer) ``is_registered()`` is ``False`` and the routes report a
    clear error rather than silently no-op'ing.
    """

    def __init__(self) -> None:
        self._start: StartPoller | None = None
        self._stop: StopPoller | None = None
        # The event loop the start/stop callables belong to. Captured by
        # web_mode at FastAPI startup (asyncio.get_running_loop()) so that
        # SYNC callers (command_executor / advisor tool / CLI) — which have
        # no event-loop handle of their own — can schedule the async
        # start/stop onto the web server's loop via run_coroutine_threadsafe.
        self._loop: asyncio.AbstractEventLoop | None = None

    def register(
        self,
        *,
        start: StartPoller,
        stop: StopPoller,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._start = start
        self._stop = stop
        self._loop = loop

    def clear(self) -> None:
        self._start = None
        self._stop = None
        self._loop = None

    def is_registered(self) -> bool:
        return self._start is not None and self._stop is not None

    async def start(self, workflow_id: int, run_id: int) -> None:
        if self._start is None:
            raise RuntimeError("dograh poller lifecycle is not registered")
        result = self._start(workflow_id, run_id)
        if asyncio.iscoroutine(result):
            await result

    async def stop(self) -> None:
        if self._stop is None:
            raise RuntimeError("dograh poller lifecycle is not registered")
        result = self._stop()
        if asyncio.iscoroutine(result):
            await result

    # --- SYNC, thread-safe triggers for non-async callers ----------------
    #
    # Calls into dograh are initiated from SYNC code (command_executor,
    # advisor tool, CLI) that has no reference to the web server's event
    # loop. These helpers bridge sync -> async safely:
    #
    #   * If a lifecycle AND its loop are registered (a web server is
    #     running), schedule the async start/stop on that loop via
    #     ``asyncio.run_coroutine_threadsafe`` and return immediately —
    #     never block on the result.
    #   * If nothing is registered (pure CLI / advisor with no web server),
    #     it's a safe no-op (debug log).
    #
    # They NEVER raise and NEVER block the caller, so wiring them into a
    # call-initiation path can't crash or hang the call.

    def request_start(self, workflow_id: int, run_id: int) -> None:
        """Schedule poller start on the registered loop, or no-op.

        Safe to call from any (sync) thread. Returns immediately.
        """
        loop = self._loop
        if not self.is_registered() or loop is None:
            logger.debug(
                "dograh request_start: no lifecycle/loop registered; no-op "
                "(workflow_id=%s run_id=%s)",
                workflow_id,
                run_id,
            )
            return
        coro = self.start(workflow_id, run_id)
        try:
            asyncio.run_coroutine_threadsafe(coro, loop)
        except Exception as exc:  # noqa: BLE001 - never crash the call path
            coro.close()  # don't leak the un-scheduled coroutine
            logger.debug("dograh request_start scheduling failed: %s", exc)

    def request_stop(self) -> None:
        """Schedule poller stop on the registered loop, or no-op.

        Safe to call from any (sync) thread. Returns immediately.
        """
        loop = self._loop
        if not self.is_registered() or loop is None:
            logger.debug("dograh request_stop: no lifecycle/loop registered; no-op")
            return
        coro = self.stop()
        try:
            asyncio.run_coroutine_threadsafe(coro, loop)
        except Exception as exc:  # noqa: BLE001 - never crash the call path
            coro.close()  # don't leak the un-scheduled coroutine
            logger.debug("dograh request_stop scheduling failed: %s", exc)


# Module-level singleton mirroring _HOLDER.
_POLLER_REGISTRY = DograhPollerRegistry()


def get_poller_registry() -> DograhPollerRegistry:
    """Return the process-wide poller-lifecycle registry."""
    return _POLLER_REGISTRY
