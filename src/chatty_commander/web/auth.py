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

from collections.abc import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html


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
    if app.docs_url is None:
        @app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url=app.openapi_url or "/openapi.json",
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            )

        @app.get("/redoc", include_in_schema=False)
        async def redoc_html():
            return get_redoc_html(
                openapi_url=app.openapi_url or "/openapi.json",
                title=app.title + " - ReDoc",
                redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            )


def apply_cors(
    app: FastAPI, *, no_auth: bool, origins: Iterable[str] | None = None
) -> None:
    """
    Apply CORS middleware consistent with legacy behavior.

    - When no_auth is True: fully permissive for local/dev usage.
    - Otherwise: restrict to provided origins, defaulting to localhost:3000.
    """
    if no_auth:
        allow_origins = ["*"]
    else:
        allow_origins = (
            list(origins) if origins is not None else ["http://localhost:3000"]
        )

    # Remove existing CORS middleware if already present to avoid duplicates.
    app.user_middleware = [
        m for m in app.user_middleware if m.cls is not CORSMiddleware
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
