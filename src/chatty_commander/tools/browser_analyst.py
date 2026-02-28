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
    allowlist = config_data.get("advisors", {}).get("browser_analyst", {}).get("allowlist", None)
    timeout = config_data.get("advisors", {}).get("browser_analyst", {}).get("timeout", 10.0)

    domain = urlparse(request.url).netloc
    if allowlist is not None and domain not in allowlist:
        logger.warning(f"Domain {domain} is not in the allowlist.")
        return AnalystResult(title="Error", summary="Domain not allowed.", url=request.url)

    try:
        response = httpx.get(request.url, timeout=timeout, follow_redirects=False)
        response.raise_for_status()
        text = response.text

        title_match = re.search(r'<title.*?>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No Title"

        # Remove script and style elements first to avoid extracting their content
        body_text = re.sub(r'<(script|style).*?>.*?</\1>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
        # Strip other HTML tags
        body_text = re.sub(r'<[^>]+>', ' ', body_text)
        # Clean whitespace
        body_text = re.sub(r'\s+', ' ', body_text).strip()

        summary = body_text[:500]

        return AnalystResult(title=title, summary=summary, url=request.url)
    except Exception as e:
        logger.error(f"Error fetching URL {request.url}: {e}")
        return AnalystResult(title="Error", summary=f"Failed to fetch: {e}", url=request.url)
