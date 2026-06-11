"""SSRF / DNS-rebinding tests for chatty_commander.utils.url_validator.

These tests stub ``socket.getaddrinfo`` to simulate an attacker-controlled
low-TTL domain that resolves to a public IP at validation time and to an
internal IP afterwards (DNS rebinding). They prove:

1. the vulnerability shape: the boolean ``is_safe_url`` API cannot prevent
   a later fetch from re-resolving to an internal address (TOCTOU), and
2. the fix: ``resolve_safe_url`` pins the validated IP into the URL so the
   fetch never performs a second DNS lookup, neutralizing rebinding.
"""

import ipaddress
import socket

import pytest

from chatty_commander.utils.url_validator import (
    is_safe_url,
)

PUBLIC_V4 = "93.184.216.34"
PUBLIC_V6 = "2606:4700:4700::1111"
INTERNAL_V4 = "127.0.0.1"


def _addrinfo(ip: str, port: int = 80):
    """Build a getaddrinfo-style result tuple for an IP string."""
    if ":" in ip:
        return (socket.AF_INET6, socket.SOCK_STREAM, 6, "", (ip, port, 0, 0))
    return (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))


class RebindingResolver:
    """Stub resolver: first lookup returns a public IP, later lookups an internal one."""

    def __init__(self, first_ip: str = PUBLIC_V4, later_ip: str = INTERNAL_V4):
        self.first_ip = first_ip
        self.later_ip = later_ip
        self.calls = 0

    def __call__(self, host, port, *args, **kwargs):
        self.calls += 1
        ip = self.first_ip if self.calls == 1 else self.later_ip
        return [_addrinfo(ip, port if isinstance(port, int) else 80)]


@pytest.fixture
def rebinding_resolver(monkeypatch):
    resolver = RebindingResolver()
    monkeypatch.setattr(socket, "getaddrinfo", resolver)
    return resolver


def _static_resolver(monkeypatch, ips):
    def resolver(host, port, *args, **kwargs):
        p = port if isinstance(port, int) else 80
        return [_addrinfo(ip, p) for ip in ips]

    monkeypatch.setattr(socket, "getaddrinfo", resolver)
    return resolver


class TestRebindingVulnerabilityShape:
    """Documents the TOCTOU window inherent to the boolean is_safe_url API."""

    def test_bool_api_cannot_stop_rebinding(self, rebinding_resolver):
        # Validation time: domain resolves to a public IP -> passes.
        assert is_safe_url("http://rebind.test/steal") is True
        assert rebinding_resolver.calls == 1

        # Fetch time: the HTTP client re-resolves the hostname itself.
        # The attacker's low-TTL record now points at an internal address.
        fetch_addrs = [
            sockaddr[0]
            for *_, sockaddr in socket.getaddrinfo("rebind.test", 80)
        ]
        assert fetch_addrs == [INTERNAL_V4]
        # i.e. a caller fetching the *hostname* URL after is_safe_url()
        # would connect to 127.0.0.1 despite validation having passed.
        assert any(
            ipaddress.ip_address(a).is_loopback for a in fetch_addrs
        )


# Pinning behaviour (resolve_safe_url / PinnedURL) is covered in
# tests/test_url_validator_rebinding.py.
