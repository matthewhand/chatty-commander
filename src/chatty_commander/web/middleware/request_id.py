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

"""Request-ID middleware for the web layer.

Canonical import point for ``RequestIdMiddleware`` used by the FastAPI app
factories. The implementation (and the contextvar that log formatters read)
lives in :mod:`chatty_commander.utils.logging_config` so that logging code can
use it without importing the web package; this module re-exports it for the
web layer alongside the other middleware in
``chatty_commander.web.middleware``.

Behavior:
- Echoes an inbound ``X-Request-ID`` header back on the response.
- Generates a UUID4 when the header is absent.
- Stores the ID in a contextvar so log records emitted while handling the
  request carry it (JSON formatters include it as ``request_id``).
"""

from __future__ import annotations

from chatty_commander.utils.logging_config import get_request_id

try:
    from chatty_commander.utils.logging_config import (
        REQUEST_ID_HEADER,
        RequestIdMiddleware,
    )
except ImportError:  # pragma: no cover - FastAPI/starlette not installed
    REQUEST_ID_HEADER = "X-Request-ID"
    RequestIdMiddleware = None  # type: ignore[assignment,misc]

__all__ = ["REQUEST_ID_HEADER", "RequestIdMiddleware", "get_request_id"]
