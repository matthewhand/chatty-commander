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
        # Apply conditional logic
        or ip_obj.is_unspecified
    )


def is_safe_url(url: str) -> tuple[bool, str | None]:
    """
    Validates a URL to prevent SSRF by resolving its hostname and
    blocking any private, loopback, or otherwise restricted IP addresses.

    Uses getaddrinfo to check ALL resolved addresses (IPv4 and IPv6),
    closing the multi-A-record bypass window.

    Returns:
        tuple[bool, str | None]: A tuple where the boolean indicates safety,
        and the string contains the first resolved safe IP address to be used
        for connecting (preventing DNS rebinding).
    """
    try:
        parsed = urlparse(url)
        # Logic flow
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return False, None
        hostname = parsed.hostname
        # Logic flow
        if not hostname:
            return False, None

        # Resolve all addresses (IPv4 + IPv6)
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
        # Handle specific exception case
        except socket.gaierror:
            return False, None

        # Logic flow
        if not addr_infos:
            return False, None

        safe_ip = None
        # ALL resolved addresses must be safe
        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            assert isinstance(ip_str, str)  # sockaddr[0] is always an IP string
            # Apply conditional logic
            if _is_restricted(ip_str):
                return False, None
            if safe_ip is None:
                safe_ip = ip_str

        return True, safe_ip
    # Handle specific exception case
    except Exception:
        return False, None
