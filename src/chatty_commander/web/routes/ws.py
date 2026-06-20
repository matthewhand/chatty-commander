# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Policy-violation close code used to reject an unauthenticated WebSocket
# handshake (RFC 6455 §7.4.1). The HTTP side answers a missing/invalid
# credential with 401; the WebSocket equivalent is to close with 1008.
WS_POLICY_VIOLATION = 1008


async def authorize_websocket(websocket: WebSocket) -> bool:
    """Authorize a WebSocket handshake, mirroring the HTTP auth degradation rule.

    The project's ``AuthMiddleware`` is a Starlette ``BaseHTTPMiddleware`` and
    therefore never sees the WebSocket scope, so ``/ws``, ``/avatar/ws`` and
    ``/ws/voice-test`` would otherwise be completely unauthenticated. This helper
    re-applies the *same* auth model the HTTP path uses, via the process-wide
    ``AuthContext`` (``web/deps/auth.py``):

    * When user auth is **not active** — ``--no-auth`` mode, no ``auth.users``
      configured, or no resolvable JWT secret — this is a **pass-through**: the
      handshake is allowed exactly as before (no regression to dev / e2e flows).
    * When user auth **is active**, a valid JWT *access* token must be supplied.
      Browsers can't set Authorization headers on a ``WebSocket``, so (matching
      what the frontend already sends — ``new WebSocket(url + "?token=<jwt>")``)
      the credential is read from the ``token`` query parameter. A missing,
      malformed, expired, revoked or wrong-type token rejects the handshake.

    Returns ``True`` if the caller should proceed to ``accept()`` the socket,
    ``False`` if it has already been rejected (closed with policy-violation).
    Never raises — a decode failure is treated as an invalid credential.
    """
    # Imported lazily so this routes module keeps importing even when the
    # optional auth dependency stack is unavailable (mirrors server.py guards).
    try:
        from ..deps.auth import (
            decode_access_token,
            get_auth_context,
            jwt_secret_for,
        )
    except ImportError:  # pragma: no cover - auth stack always present in app
        return True

    ctx = get_auth_context()
    if not ctx.is_auth_active():
        return True

    secret = jwt_secret_for(ctx.config_manager)
    if not secret:  # pragma: no cover - is_auth_active already checked this
        return True

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return False

    try:
        decode_access_token(token, secret, store=ctx.revocation_store)
    except Exception as err:  # noqa: BLE001 - any decode problem ⇒ reject
        logger.info("Rejecting WebSocket handshake: invalid token (%s)", err)
        await websocket.close(code=WS_POLICY_VIOLATION)
        return False

    return True


def include_ws_routes(
    *,
    get_connections: Callable[[], set[WebSocket]],
    set_connections: Callable[[set[WebSocket]], None],
    get_state_snapshot: Callable[[], dict[str, Any]],
    on_message: Callable[[dict[str, Any]], Any] | None = None,
    get_initial_messages: Callable[[], list[dict[str, Any]]] | None = None,
    heartbeat_seconds: float = 30.0,
) -> APIRouter:
    """
    Attach the /ws endpoint using provided accessors to avoid tight coupling.

    Providers:
      - get_connections / set_connections: manage the shared connection set
      - get_state_snapshot: returns an initial payload describing current state
      - on_message: optional callback to process inbound JSON messages
      - get_initial_messages: optional callback returning extra typed messages
        ({"type", "data", ...}) to push once on connect, after the
        ``connection_established`` snapshot — e.g. an initial ``dograh_status``
        push so push-driven cards render immediately without polling. Must
        never raise; a failure is logged and the connection proceeds.
    """
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        if not await authorize_websocket(websocket):
            return
        await websocket.accept()
        conns = get_connections()
        conns.add(websocket)
        set_connections(conns)

        try:
            # Send initial snapshot akin to legacy behavior
            snapshot = {
                "type": "connection_established",
                "data": get_state_snapshot(),
                "timestamp": datetime.now().isoformat(),
            }
            await websocket.send_text(json.dumps(snapshot))

            # Optional extra initial frames (e.g. dograh_status) so
            # push-driven cards render immediately on connect rather than
            # waiting for the first change event. Never let a producer
            # failure abort the connection.
            if get_initial_messages is not None:
                try:
                    initial_messages = get_initial_messages()
                except Exception as err:  # noqa: BLE001
                    logger.debug("get_initial_messages failed: %s", err)
                    initial_messages = []
                for message in initial_messages or []:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as err:  # noqa: BLE001
                        logger.debug("initial WS message send failed: %s", err)

            while True:
                try:
                    # Wait for incoming client messages with timeout to allow periodic heartbeats
                    data = await asyncio.wait_for(
                        websocket.receive_text(), timeout=heartbeat_seconds
                    )
                    try:
                        message = json.loads(data)
                    except Exception:
                        message = {"type": "raw", "data": data}
                    if on_message:
                        # A consumer callback failure must never tear down the
                        # connection (mirrors the initial-message producer guard
                        # above): log and continue processing further frames.
                        try:
                            on_message(message)
                        except Exception as err:  # noqa: BLE001
                            logger.debug("on_message callback failed: %s", err)

                    # Respond to ping for client keepalive symmetry
                    if isinstance(message, dict) and message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "data": {"timestamp": datetime.now().isoformat()},
                                }
                            )
                        )
                except TimeoutError:
                    # Heartbeat
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "heartbeat",
                                "data": {"timestamp": datetime.now().isoformat()},
                            }
                        )
                    )
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as err:  # noqa: BLE001
            logger.error("WebSocket error: %s", err)
        finally:
            conns = get_connections()
            conns.discard(websocket)
            set_connections(conns)

    return router
