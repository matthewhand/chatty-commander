"""Tests for SSRF / DNS-rebinding protections in url_validator.

These use a stubbed resolver (socket.getaddrinfo) so no real DNS or network
access occurs. They prove both the vulnerability shape (validation resolving
to a benign address) and the fix (the returned URL is pinned to the validated
IP, so a re-resolve to an internal address at fetch time is impossible).
"""

from __future__ import annotations

import socket

import pytest

from chatty_commander.utils import url_validator
from chatty_commander.utils.url_validator import (
    is_safe_url,
    resolve_safe_url,
)


def _addr_infos_for(ips: list[str]):
    """Build getaddrinfo-shaped tuples for the given IP strings."""
    infos = []
    for ip in ips:
        if ":" in ip:
            family = socket.AF_INET6
            sockaddr = (ip, 0, 0, 0)
        else:
            family = socket.AF_INET
            sockaddr = (ip, 0)
        infos.append((family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr))
    return infos


@pytest.fixture
def stub_resolver(monkeypatch):
    """Patch getaddrinfo to return caller-controlled IPs per hostname."""
    mapping: dict[str, list[str]] = {}

    def fake_getaddrinfo(host, port, *args, **kwargs):
        if host in mapping:
            return _addr_infos_for(mapping[host])
        raise socket.gaierror(f"unmapped host: {host}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    return mapping


def test_public_url_is_pinned_to_resolved_ip(stub_resolver):
    stub_resolver["example.com"] = ["93.184.216.34"]
    pinned = resolve_safe_url("http://example.com/path?q=1")
    assert pinned is not None
    assert pinned.ip == "93.184.216.34"
    # Pinned URL connects to the IP literal, not the hostname.
    assert pinned.url == "http://93.184.216.34/path?q=1"
    # Host header / SNI preserve the original hostname.
    assert pinned.host_header == "example.com"
    assert pinned.sni_hostname == "example.com"


def test_private_resolution_rejected(stub_resolver):
    stub_resolver["evil.example.com"] = ["169.254.169.254"]
    assert resolve_safe_url("http://evil.example.com/latest/meta-data") is None
    assert is_safe_url("http://evil.example.com/latest/meta-data") is False


def test_loopback_rejected(stub_resolver):
    stub_resolver["localhost.attacker.com"] = ["127.0.0.1"]
    assert is_safe_url("http://localhost.attacker.com") is False


def test_multi_record_any_private_is_rejected(stub_resolver):
    # One benign + one internal address: must reject (no multi-A bypass).
    stub_resolver["mixed.example.com"] = ["93.184.216.34", "10.0.0.5"]
    assert resolve_safe_url("http://mixed.example.com") is None


def test_dns_rebinding_pinning_defeats_second_resolution(stub_resolver):
    """The core TOCTOU test.

    Validation sees a benign IP. We then flip DNS to an internal IP (as a
    rebinding attacker would at fetch time). Because resolve_safe_url pins to
    the validated IP, the URL we would actually connect to still points at the
    benign address — the second resolution never gets a chance to redirect us.
    """
    host = "rebind.attacker.com"
    stub_resolver[host] = ["93.184.216.34"]  # first lookup: benign

    pinned = resolve_safe_url(f"http://{host}/")
    assert pinned is not None
    assert pinned.url == "http://93.184.216.34/"

    # Attacker flips DNS to point at the metadata service.
    stub_resolver[host] = ["169.254.169.254"]

    # A naive fetcher re-resolving the hostname would now be redirected
    # internally: demonstrate that the *hostname* now validates as unsafe...
    assert is_safe_url(f"http://{host}/") is False
    # ...but the previously pinned URL still targets the validated public IP,
    # so connecting to pinned.url cannot reach the internal address.
    assert "169.254.169.254" not in pinned.url


def test_ipv6_url_is_pinned_with_brackets(stub_resolver):
    stub_resolver["v6.example.com"] = ["2606:2800:220:1:248:1893:25c8:1946"]
    pinned = resolve_safe_url("https://v6.example.com:8443/x")
    assert pinned is not None
    assert pinned.url == "https://[2606:2800:220:1:248:1893:25c8:1946]:8443/x"
    assert pinned.host_header == "v6.example.com:8443"


def test_port_preserved_in_pinned_url(stub_resolver):
    stub_resolver["svc.example.com"] = ["93.184.216.34"]
    pinned = resolve_safe_url("http://svc.example.com:8080/api")
    assert pinned is not None
    assert pinned.url == "http://93.184.216.34:8080/api"
    assert pinned.host_header == "svc.example.com:8080"


def test_disallowed_scheme_rejected(stub_resolver):
    assert resolve_safe_url("file:///etc/passwd") is None
    assert resolve_safe_url("ftp://example.com/x") is None


def test_missing_hostname_rejected(stub_resolver):
    assert resolve_safe_url("http:///nohost") is None


def test_resolution_failure_fails_closed(stub_resolver):
    # Host not in mapping -> stub raises gaierror -> None.
    assert resolve_safe_url("http://nonexistent.example.com") is None


def test_unexpected_error_fails_closed(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("resolver exploded")

    monkeypatch.setattr(socket, "getaddrinfo", boom)
    assert resolve_safe_url("http://example.com") is None
    assert is_safe_url("http://example.com") is False


def test_is_safe_url_delegates_to_resolve(stub_resolver):
    stub_resolver["ok.example.com"] = ["93.184.216.34"]
    assert is_safe_url("http://ok.example.com") is True
    assert url_validator.is_safe_url("http://ok.example.com") is True
