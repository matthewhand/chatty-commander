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

import abc
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class AnalystRequest:
    url: str
    simulation_mode: bool = False


@dataclass
class AnalystResult:
    title: str
    summary: str
    url: str


class ContentProvider(abc.ABC):
    """Abstract base class for content providers."""

    @abc.abstractmethod
    def summarize(self, request: AnalystRequest) -> AnalystResult:
        """Fetch and summarize content from the requested URL."""
        pass


class SimulationProvider(ContentProvider):
    """Provider for simulation/dry-run mode."""

    DEFAULT_MOCK_DATA: ClassVar[dict[str, AnalystResult]] = {
        "http://example.com": AnalystResult(
            title="Example Domain",
            summary="This domain is for use in illustrative examples in documents.",
            url="http://example.com",
        )
    }

    def __init__(self, mock_data: dict[str, AnalystResult] | None = None):
        self.mock_data = mock_data or self.DEFAULT_MOCK_DATA

    def summarize(self, request: AnalystRequest) -> AnalystResult:
        if request.url in self.mock_data:
            return self.mock_data[request.url]

        # Fallback for unknown URLs in simulation mode
        return AnalystResult(
            title="Simulation Snapshot",
            summary=f"Simulated summary for {request.url}",
            url=request.url,
        )


class WebProvider(ContentProvider):
    """Real web content provider."""

    def summarize(self, request: AnalystRequest) -> AnalystResult:
        """
        Real implementation would fetch, extract, and summarize content.
        For now, this is a placeholder that would be expanded with actual requests logic.
        """
        # In a real scenario, this would use requests/httpx and BeautifulSoup/etc.
        return AnalystResult(
            title="Snapshot Title",
            summary="Snapshot Summary",
            url=request.url
        )


def summarize_url(request: AnalystRequest, provider: ContentProvider | None = None) -> AnalystResult:
    """
    Summarize a URL using the appropriate provider.

    Args:
        request: The analyst request containing the URL and options.
        provider: Optional explicit provider injection (dependency injection).
    """
    if provider:
        return provider.summarize(request)

    if request.simulation_mode:
        return SimulationProvider().summarize(request)

    return WebProvider().summarize(request)
