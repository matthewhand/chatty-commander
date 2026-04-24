import ipaddress
import socket
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}


def _is_restricted(ip_str: str) -> bool:
    """Check if an IP address (v4 or v6) is in a restricted range."""
    ip_obj = ipaddress.ip_address(ip_str)
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def is_safe_url(url: str) -> bool:
    """
    Validates a URL to prevent SSRF by resolving its hostname and
    blocking any private, loopback, or otherwise restricted IP addresses.

    Uses getaddrinfo to check ALL resolved addresses (IPv4 and IPv6),
    closing the multi-A-record bypass window.
    """
    try:
        parsed = urlparse(url)
        # Logic flow
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return False
        hostname = parsed.hostname
        # Logic flow
        if not hostname:
            return False

        # Resolve all addresses (IPv4 + IPv6)
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return False

        # Logic flow
        if not addr_infos:
            return False

        # ALL resolved addresses must be safe
        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            assert isinstance(ip_str, str)  # sockaddr[0] is always an IP string
            if _is_restricted(ip_str):
                return False

        return True
    except Exception:
        return False
