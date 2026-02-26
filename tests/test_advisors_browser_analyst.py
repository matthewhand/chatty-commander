import pytest
from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool


def test_browser_analyst_github():
    url = "https://github.com/example/repo"
    result = browser_analyst_tool(url)
    assert "GitHub repository:" in result
    assert "open source project" in result


def test_browser_analyst_stackoverflow():
    url = "https://stackoverflow.com/questions/123"
    result = browser_analyst_tool(url)
    assert "Stack Overflow question:" in result
    assert "programming questions and answers" in result


def test_browser_analyst_wikipedia():
    url = "https://wikipedia.org/wiki/Example"
    result = browser_analyst_tool(url)
    assert "Wikipedia article:" in result
    assert "encyclopedia entry" in result


def test_browser_analyst_generic():
    url = "https://example.com"
    result = browser_analyst_tool(url)
    assert "Web page at" in result
    assert "general web page" in result


def test_browser_analyst_error_handling():
    url = None
    result = browser_analyst_tool(url)
    assert "Unable to analyze" in result
    assert "due to an error" in result
