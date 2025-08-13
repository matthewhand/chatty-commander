from chatty_commander.tools.browser_analyst import AnalystRequest, summarize_url


def test_summarize_url_returns_deterministic_result():
    req = AnalystRequest(url="https://example.com/test")
    result = summarize_url(req)
    assert result.title == "Snapshot Title"
    assert result.summary.startswith("Snapshot")
    assert result.url.endswith("/test")
