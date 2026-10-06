"""SSRF protection for the Tier-3 adaptive extraction path (§9/§13).

This module has NO Django imports and NO third-party dependencies (pure
stdlib: urllib.parse, socket, ipaddress) so the exact same validation logic
can be used from TWO places without import coupling:

  1. apps/scraper/pipeline/extraction_adapter.py's OutOfProcessBackend -
     the Django-side enforcement point, checked BEFORE a subprocess/
     container is ever launched. This is the primary, always-applied gate
     for the real production wiring.
  2. apps/scraper/extraction_runners/scrapling_runner.py - the standalone
     out-of-process script itself re-validates independently (duplicated,
     not imported, because that script's own docstring requires "zero
     Django imports, zero dependency on the main backend package" so it can
     run in a separate isolated venv/container). This is defense-in-depth:
     the script could in principle be invoked directly (e.g. a bare
     `docker run usam-scrapling-runner` with attacker-controlled stdin),
     bypassing the Django-side gate entirely.

WHY THIS EXISTS: before this module, scrapling_runner.py accepted ANY URL
from its stdin JSON payload with zero validation and handed it straight to
Scrapling's Fetcher/StealthyFetcher. A Source row (admin-creatable via the
API) or a future less-trusted input path (e.g. source rediscovery feeding a
URL back into the adaptive tier) could point this at:
  - http://127.0.0.1:<internal-port>/...        (loopback - any local service)
  - http://169.254.169.254/latest/meta-data/...  (cloud metadata endpoint -
    AWS/GCP/Azure instance credentials theft, the single most common SSRF
    payload against anything running on EC2/GCE/Azure VMs, which this
    platform does)
  - http://10.x.x.x / 172.16-31.x.x / 192.168.x.x (RFC1918 private networks -
    reach Postgres/Redis/Typesense/internal admin panels directly)
  - file:///etc/passwd, ftp://..., etc.          (non-HTTP schemes)
and the out-of-process extractor would happily fetch it, exfiltrating
whatever that internal service returns back through the "jobs" response.

RESIDUAL RISK (documented, not hidden): this validates the URL's hostname at
the time of the request. It does NOT re-validate each hop of an HTTP
redirect chain - a classic SSRF bypass is "https://attacker.com/x resolves
to a public IP and passes this check, then redirects to http://127.0.0.1/y".
Scrapling's underlying fetchers (curl_cffi / Playwright) follow redirects
internally without exposing a per-hop callback this module can hook. Fully
closing that gap would require either disabling redirect-following entirely
(breaking many legitimate careers-page redirects) or vendoring a custom HTTP
client - out of scope for this hardening pass. This is flagged explicitly
rather than silently claimed as fully solved.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# Only plain HTTP/HTTPS may be fetched. file://, ftp://, gopher://, data://,
# etc. are never valid "fetch this careers page" requests.
ALLOWED_SCHEMES = frozenset({"http", "https"})

# Hostnames that are never a legitimate external careers-page target,
# checked by exact match before any DNS resolution happens (cheap, catches
# the most common literal SSRF payloads without a network round-trip).
BLOCKED_HOSTNAMES = frozenset({
    "localhost", "localhost.localdomain", "metadata.google.internal",
})


@dataclass
class UrlSafetyResult:
    safe: bool
    reason: str = ""
    resolved_ip: Optional[str] = None


def _is_blocked_ip(ip_str: str) -> Optional[str]:
    """Return a human-readable block reason if `ip_str` is a non-public
    address (loopback / private / link-local incl. cloud metadata / reserved
    / multicast), else None."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return "unparseable IP address"

    if ip.is_loopback:
        return f"loopback address ({ip_str})"
    if ip.is_private:
        return f"private/RFC1918 address ({ip_str})"
    if ip.is_link_local:
        # Covers 169.254.0.0/16 (IPv4) and fe80::/10 (IPv6) - this is where
        # the AWS/GCP/Azure instance metadata endpoint (169.254.169.254)
        # lives, the single highest-value SSRF target on any cloud VM.
        return f"link-local address incl. cloud metadata range ({ip_str})"
    if ip.is_reserved:
        return f"reserved address ({ip_str})"
    if ip.is_multicast:
        return f"multicast address ({ip_str})"
    if ip.is_unspecified:
        return f"unspecified address ({ip_str})"
    return None


def validate_url_safe(url: str, *, resolver=None) -> UrlSafetyResult:
    """Validate that `url` is safe to fetch from a server-side extractor.

    `resolver` is injected for testability (defaults to socket.getaddrinfo);
    tests supply a fake resolver so this runs offline without real DNS.
    """
    if not url or not isinstance(url, str):
        return UrlSafetyResult(safe=False, reason="empty or non-string URL")

    try:
        parsed = urlparse(url)
    except ValueError as e:
        return UrlSafetyResult(safe=False, reason=f"unparseable URL: {e}")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return UrlSafetyResult(safe=False, reason=f"disallowed scheme: {scheme!r} (only http/https allowed)")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return UrlSafetyResult(safe=False, reason="URL has no hostname")

    if hostname in BLOCKED_HOSTNAMES:
        return UrlSafetyResult(safe=False, reason=f"blocked hostname literal: {hostname!r}")

    # A bare IP literal in the URL - check it directly without a DNS call.
    try:
        literal_ip = ipaddress.ip_address(hostname.strip("[]"))
        block_reason = _is_blocked_ip(str(literal_ip))
        if block_reason:
            return UrlSafetyResult(safe=False, reason=block_reason, resolved_ip=str(literal_ip))
        return UrlSafetyResult(safe=True, resolved_ip=str(literal_ip))
    except ValueError:
        pass  # not a bare IP literal - resolve the hostname below

    # Resolve the hostname and check EVERY returned address - a hostname can
    # have multiple A/AAAA records, and an attacker-controlled DNS name could
    # intentionally return a mix hoping only the first is checked.
    _resolver = resolver or (lambda host: socket.getaddrinfo(host, None))
    try:
        addrinfo = _resolver(hostname)
    except (socket.gaierror, OSError) as e:
        return UrlSafetyResult(safe=False, reason=f"DNS resolution failed: {type(e).__name__}: {e}")

    if not addrinfo:
        return UrlSafetyResult(safe=False, reason="DNS resolution returned no addresses")

    resolved_ips = []
    for entry in addrinfo:
        # getaddrinfo entries are (family, type, proto, canonname, sockaddr);
        # sockaddr[0] is the IP string for both AF_INET and AF_INET6.
        ip_str = entry[4][0]
        resolved_ips.append(ip_str)
        block_reason = _is_blocked_ip(ip_str)
        if block_reason:
            return UrlSafetyResult(safe=False, reason=f"resolves to {block_reason}", resolved_ip=ip_str)

    return UrlSafetyResult(safe=True, resolved_ip=resolved_ips[0] if resolved_ips else None)
