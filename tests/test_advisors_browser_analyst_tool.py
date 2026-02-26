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

import pytest
from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool


def test_browser_analyst_github():
    """Test that GitHub URLs are correctly identified and summarized."""
    url = "https://github.com/mhand/chatty-commander"
    result = browser_analyst_tool(url)
    assert "GitHub repository" in result
    assert url in result
    assert "open source project" in result


def test_browser_analyst_stackoverflow():
    """Test that StackOverflow URLs are correctly identified and summarized."""
    url = "https://stackoverflow.com/questions/12345678/test-question"
    result = browser_analyst_tool(url)
    assert "Stack Overflow question" in result
    assert url in result
    assert "programming questions" in result


def test_browser_analyst_wikipedia():
    """Test that Wikipedia URLs are correctly identified and summarized."""
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    result = browser_analyst_tool(url)
    assert "Wikipedia article" in result
    assert url in result
    assert "encyclopedia entry" in result


def test_browser_analyst_generic():
    """Test that generic URLs are handled with a default summary."""
    url = "https://example.com"
    result = browser_analyst_tool(url)
    assert "Web page at" in result
    assert url in result
    assert "general web page" in result


def test_browser_analyst_error():
    """Test that errors during analysis are handled gracefully."""
    # Passing None to trigger an exception (as 'in' operator requires iterable)
    # The function expects a string, so this violates type hint but tests error handler
    result = browser_analyst_tool(None)  # type: ignore
    assert "Unable to analyze" in result
    assert "due to an error" in result
