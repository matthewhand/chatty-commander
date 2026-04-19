from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool


@pytest.mark.perf
def test_browser_analyst_tool_perf(benchmark):
    mock_response = MagicMock()
    # Simulate a stream that has many chunks.
    # Total size around 1 MB. 1 MB / 8 KB = 125 chunks.
    chunk_data = b"a" * 8192
    mock_response.encoding = "utf-8"

    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_response
    mock_context_manager.__exit__.return_value = None

    def stream_mock(*args, **kwargs):
        mock_response.iter_bytes.return_value = (chunk_data for _ in range(125))
        return mock_context_manager

    with (
        patch(
            "chatty_commander.advisors.tools.browser_analyst.httpx.stream",
            side_effect=stream_mock,
        ),
        patch(
            "chatty_commander.advisors.tools.browser_analyst.is_safe_url",
            return_value=True,
        ),
        patch("chatty_commander.advisors.tools.browser_analyst.Config") as MockConfig,
    ):

        mock_config_instance = MagicMock()
        mock_config_instance.config_data = {}
        MockConfig.return_value = mock_config_instance

        # ⚡ Bolt: Benchmark the HTTP stream processing and regex
        benchmark(browser_analyst_tool, "https://example.com")
