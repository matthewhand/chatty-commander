from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.advisors.tools.browser_analyst import browser_analyst_tool


@pytest.mark.perf
def test_browser_analyst_tool_perf(request):
    """Perf test guarded so broad runs (no pytest-benchmark) skip instead of error."""
    try:
        benchmark = request.getfixturevalue("benchmark")
    except Exception:
        pytest.skip("pytest-benchmark not available (install pytest-benchmark to run perf)")
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

    # The tool now connects via an IP-pinned httpx.Client (DNS-rebinding
    # hardening), so mock the Client and its .stream(), and the URL resolver.
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.stream.side_effect = stream_mock

    pinned = MagicMock()
    pinned.url = "https://93.184.216.34"
    pinned.host_header = "example.com"
    pinned.sni_hostname = "example.com"

    with (
        patch(
            "chatty_commander.advisors.tools.browser_analyst.httpx.Client",
            return_value=mock_client,
        ),
        patch(
            "chatty_commander.advisors.tools.browser_analyst.resolve_safe_url",
            return_value=pinned,
        ),
        patch("chatty_commander.advisors.tools.browser_analyst.Config") as MockConfig,
    ):

        mock_config_instance = MagicMock()
        mock_config_instance.config_data = {}
        MockConfig.return_value = mock_config_instance

        # ⚡ Bolt: Benchmark the HTTP stream processing and regex
        benchmark(browser_analyst_tool, "https://example.com")
