import socket
from unittest.mock import patch

from chatty_commander.utils.url_validator import _is_restricted, is_safe_url


def test_is_restricted():
    assert _is_restricted("127.0.0.1") is True
    assert _is_restricted("192.168.1.1") is True
    assert _is_restricted("10.0.0.1") is True
    assert _is_restricted("169.254.169.254") is True
    assert _is_restricted("0.0.0.0") is True
    assert _is_restricted("::1") is True

    # Public IPs should not be restricted
    assert _is_restricted("8.8.8.8") is False
    assert _is_restricted("1.1.1.1") is False


def test_is_safe_url_bad_scheme():
    assert is_safe_url("ftp://example.com") is False
    assert is_safe_url("file:///etc/passwd") is False


def test_is_safe_url_no_hostname():
    assert is_safe_url("https://") is False


@patch("socket.getaddrinfo")
def test_is_safe_url_dns_error(mock_getaddrinfo):
    mock_getaddrinfo.side_effect = socket.gaierror("Mock error")
    assert is_safe_url("https://nonexistent.example.com") is False


@patch("socket.getaddrinfo")
def test_is_safe_url_no_results(mock_getaddrinfo):
    mock_getaddrinfo.return_value = []
    assert is_safe_url("https://empty.example.com") is False


@patch("socket.getaddrinfo")
def test_is_safe_url_restricted_ip(mock_getaddrinfo):
    # Mock returning a private IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.100", 443))
    ]
    assert is_safe_url("https://internal.example.com") is False


@patch("socket.getaddrinfo")
def test_is_safe_url_safe_ip(mock_getaddrinfo):
    # Mock returning a public IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
    ]
    assert is_safe_url("https://safe.example.com") is True


def test_is_safe_url_exception():
    # Force an exception during urlparse
    assert is_safe_url(None) is False
