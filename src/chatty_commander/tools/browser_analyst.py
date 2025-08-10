from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalystRequest:
    url: str


@dataclass
class AnalystResult:
    title: str
    summary: str
    url: str


def summarize_url(request: AnalystRequest) -> AnalystResult:
    """Deterministic placeholder that avoids network for tests.

    Real implementation would fetch, extract, and summarize content with allowlists and timeouts.
    """
    # Minimal deterministic result for tests
    return AnalystResult(title="Snapshot Title", summary="Snapshot Summary", url=request.url)


