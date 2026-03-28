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

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI


def register_lifecycle(
    app: FastAPI,
    *,
    get_state_manager: Callable[[], Any],
    on_startup: Callable[[], None] | None = None,
    on_shutdown: Callable[[], None] | None = None,
) -> None:
    """
    Register minimal startup/shutdown hooks using provider callables.

    Notes:
    - Defaults are no-ops to preserve existing behavior.
    - We do not modify or duplicate any callbacks that legacy WebModeServer already registers.
    - This provides a stable boundary to extend later without impacting current tests.
    """

    @app.on_event("startup")
    async def _startup() -> None:  # noqa: D401
        # Intentionally minimal; invoke optional callback if present.
        if on_startup is not None:
            try:
                on_startup()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # noqa: D401
        # Intentionally minimal; invoke optional callback if present.
        if on_shutdown is not None:
            try:
                on_shutdown()
            except Exception:
                # Keep behavior non-fatal and consistent with legacy tolerance.
                pass
