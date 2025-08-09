"""
Lightweight browser analyst tool used by AdvisorsService summarize command.

This stub avoids network calls and returns a deterministic summary string for tests.
"""


def browser_analyst_tool(url: str) -> str:
    """
    Return a short, deterministic summary for the provided URL.

    Args:
        url: The URL to summarize.

    Returns:
        A single-line summary string suitable for inclusion in responses.
    """
    return f"A concise overview of {url} for testing purposes."