import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}


def _is_restricted(ip_str: str) -> bool:
    ip_obj = ipaddress.ip_address(ip_str)
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


@dataclass(frozen=True)
class PinnedURL:
    """A validated URL pinned to the IP address that passed validation.

    Connecting to ``url`` (whose host is an IP literal) instead of the
    original URL closes the DNS-rebinding TOCTOU window: the fetch can no
    longer re-resolve the hostname to a different (internal) address after
    validation.

    Usage with httpx (works for both HTTP and HTTPS; ``sni_hostname`` makes
    TLS SNI and certificate verification use the original hostname)::

        pinned = resolve_safe_url(url)
        if pinned is None:
            ...  # reject
        client.get(
            pinned.url,
            headers={"Host": pinned.host_header},
            extensions={"sni_hostname": pinned.sni_hostname},
        )
    """

    url: str
    """The original URL with its host replaced by the validated IP literal."""
    ip: str
    """The validated IP address the connection should be made to."""
    host_header: str
    """Value for the HTTP ``Host`` header (original host, plus explicit port)."""
    sni_hostname: str
    """Original hostname, for TLS SNI / certificate verification."""


def resolve_safe_url(url: str) -> PinnedURL | None:
    """
    Validate a URL against SSRF and return it pinned to the resolved IP.

    Resolves the hostname once, requires ALL resolved addresses (IPv4 and
    IPv6) to be non-restricted, and returns a :class:`PinnedURL` whose host
    is one of the validated IP literals. Fetching the pinned URL cannot be
    redirected by DNS rebinding because no second DNS lookup takes place.

    Returns ``None`` (fail closed) for disallowed schemes, missing/invalid
    hosts, resolution failures, or any restricted resolved address.

    Note: any userinfo (``user:pass@``) in the URL is dropped from the
    pinned URL.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return None
        hostname = parsed.hostname
        if not hostname:
            return None
        port = parsed.port  # raises ValueError for out-of-range ports

        # Resolve all addresses (IPv4 + IPv6)
        try:
            addr_infos = socket.getaddrinfo(
                hostname,
                port or (443 if parsed.scheme == "https" else 80),
                proto=socket.IPPROTO_TCP,
            )
        except (socket.gaierror, TimeoutError):
            return None

        if not addr_infos:
            return None

        # ALL resolved addresses must be safe (multi-record bypass guard)
        ips: list[str] = []
        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            assert isinstance(ip_str, str)  # sockaddr[0] is always an IP string
            if _is_restricted(ip_str):
                return None
            ips.append(ip_str)

        pinned_ip = ips[0]
        url_host = f"[{pinned_ip}]" if ":" in pinned_ip else pinned_ip
        netloc = url_host if port is None else f"{url_host}:{port}"
        header_host = f"[{hostname}]" if ":" in hostname else hostname
        host_header = header_host if port is None else f"{header_host}:{port}"
        return PinnedURL(
            url=urlunparse(parsed._replace(netloc=netloc)),
            ip=pinned_ip,
            host_header=host_header,
            sni_hostname=hostname,
        )
    except Exception as e:
        # Fail closed (treat as unsafe), but surface unexpected errors so an
        # operator can notice resolver/parsing problems rather than silently
        # rejecting (or, worse, masking) URLs.
        logger.warning("URL safety check failed unexpectedly for %r: %s", url, e)
        return None


def is_safe_url(url: str) -> bool:
    """
    Validates a URL to prevent SSRF by resolving its hostname and
    blocking any private, loopback, or otherwise restricted IP addresses.

    Uses getaddrinfo to check ALL resolved addresses (IPv4 and IPv6),
    closing the multi-A-record bypass window.

    WARNING (TOCTOU / DNS rebinding): this check resolves the hostname, but
    a subsequent fetch of the original URL performs its own DNS lookup. An
    attacker-controlled, low-TTL domain can pass this check and then
    re-resolve to an internal address at connect time. Callers fetching
    untrusted URLs should use :func:`resolve_safe_url` and connect to the
    pinned IP instead of re-fetching the hostname URL.
    """
    return resolve_safe_url(url) is not None
