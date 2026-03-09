import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_url(url: str) -> bool:
    """
    Validates a URL to prevent SSRF by resolving its hostname and
    blocking any private, loopback, or otherwise restricted IP addresses.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        # Attempt to resolve hostname to IP
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False  # Cannot resolve

        ip_obj = ipaddress.ip_address(ip)

        # Check against restricted ranges
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return False

        return True
    except Exception:
        return False
