from unittest.mock import patch, MagicMock


def test_execute_command_url(setup_executor):
    """Test URL command execution."""
    setup_executor.config.model_actions["test_url"] = {"url": "http://example.com"}
    with patch.object(setup_executor, "_execute_url") as mock_url:
        mock_url.return_value = True
        result = setup_executor.execute_command("test_url")
        assert result is True
        mock_url.assert_called_once_with("test_url", "http://example.com")


def test_execute_command_new_format_url(setup_executor):
    """Test execute_command with new format url action."""
    setup_executor.config.model_actions = {
        "test_cmd": {"action": "url", "url": "http://example.com"}
    }
    with patch.object(setup_executor, "_execute_url") as mock_url:
        mock_url.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_url.assert_called_once_with("test_cmd", "http://example.com")


def test_execute_command_old_format_url(setup_executor):
    """Test execute_command with old format url action."""
    setup_executor.config.model_actions = {"test_cmd": {"url": "http://example.com"}}
    with patch.object(setup_executor, "_execute_url") as mock_url:
        mock_url.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_url.assert_called_once_with("test_cmd", "http://example.com")


def test_execute_url_empty_url(setup_executor):
    """Test _execute_url with empty URL."""
    with patch.object(setup_executor, "report_error") as mock_report:
        setup_executor._execute_url("test_cmd", "")
        mock_report.assert_called_once_with("test_cmd", "missing URL")


def test_execute_url_no_requests(setup_executor):
    """Expect DependencyError when requests is missing."""
    from chatty_commander.exceptions import DependencyError
    with patch("chatty_commander.app.command_executor.requests", None):
        with pytest.raises(DependencyError):
            setup_executor._execute_url("test_cmd", "http://example.com")(setup_executor):
    """Test _execute_url when requests is not available."""
    with patch("chatty_commander.app.command_executor.requests", None):
        with patch.object(setup_executor, "report_error") as mock_report:
            setup_executor._execute_url("test_cmd", "http://example.com")
            mock_report.assert_called_once_with("test_cmd", "requests not available")


def test_execute_url_http_error(setup_executor):
    """Test _execute_url with HTTP error response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch("chatty_commander.app.command_executor.requests") as mock_requests:
        mock_requests.get.return_value = mock_response
        with patch.object(setup_executor, "report_error") as mock_report:
            setup_executor._execute_url("test_cmd", "http://example.com")
            mock_report.assert_called_once_with("test_cmd", "http 404")


def test_execute_url_exception(setup_executor):
    """Expect ExecutionError when requests.get raises."""
    from chatty_commander.exceptions import ExecutionError
    with patch("chatty_commander.app.command_executor.requests") as mock_requests:
        mock_requests.get.side_effect = Exception("Connection error")
        with pytest.raises(ExecutionError):
            setup_executor._execute_url("test_cmd", "http://example.com")(setup_executor):
    """Test _execute_url exception handling."""
    with patch("chatty_commander.app.command_executor.requests") as mock_requests:
        mock_requests.get.side_effect = Exception("Connection error")
        with patch.object(setup_executor, "report_error") as mock_report:
            setup_executor._execute_url("test_cmd", "http://example.com")
            mock_report.assert_called_once_with("test_cmd", "Connection error")
