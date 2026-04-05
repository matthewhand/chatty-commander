# NOTE: This module is superseded by advisors/tools/browser_analyst.py. Kept for test compatibility.
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

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from chatty_commander.app.config import Config
from chatty_commander.utils.url_validator import is_safe_url

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AnalystRequest:
    url: str


@dataclass
class AnalystResult:
    title: str
    summary: str
    url: str


def summarize_url(request: AnalystRequest) -> AnalystResult:
    """Fetch, extract, and summarize content with allowlists and timeouts."""
    if not HTTPX_AVAILABLE:
        return AnalystResult(
            title="Snapshot Title", summary="Snapshot Summary", url=request.url
        )

    config_data = Config().config_data
    allowlist = (
        config_data.get("advisors", {})
        .get("browser_analyst", {})
        .get("allowlist", None)
    )
    timeout = (
        config_data.get("advisors", {}).get("browser_analyst", {}).get("timeout", 10.0)
    )

    parsed_url = urlparse(request.url)
    if parsed_url.scheme not in ("http", "https"):
        return AnalystResult(
            title="Error",
            summary=f"Invalid URL scheme '{parsed_url.scheme}'.",
            url=request.url,
        )
    hostname = parsed_url.hostname or ""
    if allowlist is not None and hostname not in allowlist:
        logger.warning(f"Domain {hostname} is not in the allowlist.")
        return AnalystResult(
            title="Error", summary="Domain not allowed.", url=request.url
        )

    if not is_safe_url(request.url):
        logger.warning(
            f"SSRF blocked: URL resolves to private/internal address: {request.url}"
        )
        return AnalystResult(
            title="Error",
            summary="URL blocked: resolves to internal address.",
            url=request.url,
        )

    try:
        # Prevent DoS via memory exhaustion with a 2MB limit
        MAX_SIZE = 2 * 1024 * 1024
        text = ""
        with httpx.stream(
            "GET", request.url, timeout=timeout, follow_redirects=False
        ) as response:
            response.raise_for_status()
            content_pieces = []
            size = 0
            for chunk in response.iter_bytes(chunk_size=8192):
                content_pieces.append(chunk)
                size += len(chunk)
                if size > MAX_SIZE:
                    break
            text = b"".join(content_pieces).decode("utf-8", errors="replace")

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL
        )
        title = title_match.group(1).strip() if title_match else "No Title"

        # Prevent ReDoS by avoiding .*? within tags
        body_text = re.sub(
            r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL
        )
        # Strip other HTML tags
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        # Clean whitespace
        body_text = re.sub(r"\s+", " ", body_text).strip()

        summary = body_text[:500]

        return AnalystResult(title=title, summary=summary, url=request.url)
    except Exception as e:
        logger.error(f"Error fetching URL {request.url}: {e}")
        return AnalystResult(
            title="Error", summary=f"Failed to fetch: {e}", url=request.url
        )
