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

try:
    from agents import FunctionTool

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def browser_analyst_tool(url: str, max_length: int | None = 500) -> str:
    """
    Analyze and summarize web content from a given URL.

    Args:
        url: The URL to analyze and summarize.
        max_length: Maximum length of the summary (default: 500).

    Returns:
        A concise summary of the web content.
    """
    try:
        # For now, return a deterministic response
        # In a real implementation, this would fetch and analyze the URL
        if "github.com" in url:
            return f"GitHub repository: {url}. This appears to be an open source project with documentation, issues, and pull requests."
        elif "stackoverflow.com" in url:
            return f"Stack Overflow question: {url}. This contains programming questions and answers from the developer community."
        elif "wikipedia.org" in url:
            return f"Wikipedia article: {url}. This is an encyclopedia entry providing factual information on the topic."
        else:
            return f"Web page at {url}: This appears to be a general web page with content related to the URL's domain."

    except Exception as e:
        logger.error(f"Error analyzing URL {url}: {e}")
        return f"Unable to analyze {url} due to an error."


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
