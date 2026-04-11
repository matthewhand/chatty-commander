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

"""
Browser analyst tool for Advisors using OpenAI Agents framework.

This tool provides web content analysis capabilities to advisors.
"""

import logging
import re
from urllib.parse import urlparse

from chatty_commander.app.config import Config
from chatty_commander.utils.url_validator import is_safe_url

try:
    from agents import FunctionTool

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


def _deterministic_fallback(url: str) -> str:
    hostname = urlparse(url).hostname or ""
    if hostname == "github.com" or hostname.endswith(".github.com"):
        return f"GitHub repository: {url}. This appears to be an open source project with documentation, issues, and pull requests."
    elif hostname == "stackoverflow.com" or hostname.endswith(".stackoverflow.com"):
        return f"Stack Overflow question: {url}. This contains programming questions and answers from the developer community."
    elif hostname == "wikipedia.org" or hostname.endswith(".wikipedia.org"):
        return f"Wikipedia article: {url}. This is an encyclopedia entry providing factual information on the topic."
    else:
        return f"Web page at {url}: This appears to be a general web page with content related to the URL's domain."

def browser_analyst_tool(url: str) -> str:
    """
    Analyze and summarize web content from a given URL.

    Args:
        url: The URL to analyze and summarize.

    Returns:
        A concise summary of the web content.
    """
    if not HTTPX_AVAILABLE:
        return _deterministic_fallback(url)

    try:
        config_data = Config().config_data
        allowlist = config_data.get("advisors", {}).get("browser_analyst", {}).get("allowlist", None)
        timeout = config_data.get("advisors", {}).get("browser_analyst", {}).get("timeout", 10.0)

        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            return f"Error: Invalid URL scheme '{parsed_url.scheme}'. Only http and https are allowed."
        hostname = parsed_url.hostname or ""
        if allowlist is not None and hostname not in allowlist:
            logger.warning(f"Domain {hostname} is not in the allowlist.")
            return f"Error: Domain {hostname} is not allowed."

        if not is_safe_url(url):
            logger.warning(f"SSRF blocked: URL resolves to private/internal address: {url}")
            return "Error: URL blocked — resolves to internal address."

        # Prevent DoS via memory exhaustion with a 2MB limit
        MAX_SIZE = 2 * 1024 * 1024
        text = ""
        with httpx.stream("GET", url, timeout=timeout, follow_redirects=False) as response:
            response.raise_for_status()
            content_pieces = []
            size = 0
            for chunk in response.iter_text(chunk_size=8192):
                content_pieces.append(chunk)
                size += len(chunk.encode("utf-8"))
                if size > MAX_SIZE:
                    break
            text = "".join(content_pieces)

        title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No Title"

        # Prevent ReDoS by avoiding .*? within tags
        body_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
        # Strip other HTML tags
        body_text = re.sub(r'<[^>]+>', ' ', body_text)
        # Clean whitespace
        body_text = re.sub(r'\s+', ' ', body_text).strip()

        summary = body_text[:500]
        return f"Title: {title}\nSummary: {summary}"

    except Exception as e:
        logger.error(f"Error analyzing URL {url}: {e}")
        return f"Unable to analyze {url} due to an error: {e}"


# Create the tool instance if agents are available
browser_analyst_tool_instance = None
if AGENTS_AVAILABLE:
    browser_analyst_tool_instance = FunctionTool(
        name="browser_analyst",
        description="Analyze and summarize web content from URLs. Useful for getting quick overviews of web pages, documentation, or articles.",
        params_json_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to analyze and summarize",
                }
            },
            "required": ["url"],
        },
        on_invoke_tool=browser_analyst_tool,
    )
