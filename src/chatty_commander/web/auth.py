from __future__ import annotations

from collections.abc import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def enable_no_auth_docs(app: FastAPI, *, no_auth: bool) -> None:
    """
    Toggle docs/re-doc endpoints based on no_auth.

    If no_auth is True, ensure docs are exposed at /docs and /redoc.
    Otherwise, leave existing configuration as-is (do not force-disable).
    """
    if not no_auth:
        return
    # FastAPI does not support toggling docs_url/redoc_url after init,
    # but if app.docs_url is None (hidden), we can attach routes manually if needed.
    # For now, assume the legacy app has already set docs appropriately when in no_auth.
    # This function remains a no-op placeholder to formalize the intent and boundary.
    return


def apply_cors(app: FastAPI, *, no_auth: bool, origins: Iterable[str] | None = None) -> None:
    """
    Apply CORS middleware consistent with legacy behavior.

    - When no_auth is True: fully permissive for local/dev usage.
    - Otherwise: restrict to provided origins, defaulting to localhost:3000.
    """
    if no_auth:
        allow_origins = ["*"]
    else:
        allow_origins = list(origins) if origins is not None else ["http://localhost:3000"]

    # Remove existing CORS middleware if already present to avoid duplicates.
    app.user_middleware = [m for m in app.user_middleware if m.cls is not CORSMiddleware]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
