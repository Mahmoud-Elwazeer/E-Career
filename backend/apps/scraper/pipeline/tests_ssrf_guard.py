"""Tests for ssrf_guard.py (§9/§13 Scrapling production safety hardening).

Pure-Python, no Django/network dependency - DNS resolution is injected via
a fake resolver so these run fully offline.
"""
from apps.scraper.pipeline.ssrf_guard import validate_url_safe, _is_blocked_ip


def _fake_resolver(mapping):
    """Build a resolver matching socket.getaddrinfo's return shape:
    list of (family, type, proto, canonname, (ip, port))."""
    def resolver(host):
        ip = mapping.get(host)
        if ip is None:
            raise OSError(f"no mapping for {host}")
        return [(2, 1, 6, "", (ip, 0))]
    return resolver


# --- scheme checks ---

def test_https_allowed():
    r = validate_url_safe("https://example.com/careers", resolver=_fake_resolver({"example.com": "93.184.216.34"}))
    assert r.safe is True


def test_http_allowed():
    r = validate_url_safe("http://example.com/careers", resolver=_fake_resolver({"example.com": "93.184.216.34"}))
    assert r.safe is True


def test_file_scheme_blocked():
    r = validate_url_safe("file:///etc/passwd")
    assert r.safe is False
    assert "scheme" in r.reason


def test_ftp_scheme_blocked():
    r = validate_url_safe("ftp://example.com/secret")
    assert r.safe is False
    assert "scheme" in r.reason


def test_empty_url_blocked():
    r = validate_url_safe("")
    assert r.safe is False


# --- literal hostname/IP checks (no DNS needed) ---

def test_localhost_hostname_blocked():
    r = validate_url_safe("http://localhost:8000/admin")
    assert r.safe is False
    assert "localhost" in r.reason


def test_loopback_ip_literal_blocked():
    r = validate_url_safe("http://127.0.0.1:8000/")
    assert r.safe is False
    assert "loopback" in r.reason


def test_aws_metadata_ip_literal_blocked():
    """The single highest-value SSRF target on any cloud VM. Python's
    ipaddress.is_private already classifies 169.254.0.0/16 as private
    (link-local is a subset IANA also marks private-use), so the guard
    blocks it via the "private" branch before even reaching the explicit
    is_link_local check - the important thing is it's blocked at all."""
    r = validate_url_safe("http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    assert r.safe is False
    assert r.resolved_ip == "169.254.169.254"


def test_rfc1918_10_blocked():
    r = validate_url_safe("http://10.0.5.23/internal")
    assert r.safe is False
    assert "private" in r.reason


def test_rfc1918_172_blocked():
    r = validate_url_safe("http://172.16.0.1/internal")
    assert r.safe is False
    assert "private" in r.reason


def test_rfc1918_192_168_blocked():
    r = validate_url_safe("http://192.168.1.1/internal")
    assert r.safe is False
    assert "private" in r.reason


def test_public_ip_literal_allowed():
    r = validate_url_safe("http://93.184.216.34/careers")
    assert r.safe is True


# --- DNS-resolved hostname checks ---

def test_hostname_resolving_to_public_ip_allowed():
    r = validate_url_safe(
        "https://careers.example.com/jobs",
        resolver=_fake_resolver({"careers.example.com": "93.184.216.34"}),
    )
    assert r.safe is True
    assert r.resolved_ip == "93.184.216.34"


def test_hostname_resolving_to_private_ip_blocked():
    """The classic DNS-rebinding-style SSRF: a hostname an attacker controls
    (or a misconfigured internal DNS entry) resolves to a private address."""
    r = validate_url_safe(
        "https://internal-looking.example.com/x",
        resolver=_fake_resolver({"internal-looking.example.com": "10.1.2.3"}),
    )
    assert r.safe is False
    assert "private" in r.reason


def test_hostname_resolving_to_metadata_ip_blocked():
    r = validate_url_safe(
        "https://attacker-controlled.example.com/x",
        resolver=_fake_resolver({"attacker-controlled.example.com": "169.254.169.254"}),
    )
    assert r.safe is False


def test_dns_resolution_failure_is_unsafe_not_crash():
    r = validate_url_safe("https://this-does-not-resolve.invalid/x", resolver=_fake_resolver({}))
    assert r.safe is False
    assert "DNS resolution failed" in r.reason


# --- _is_blocked_ip unit coverage ---

def test_is_blocked_ip_reserved_and_multicast():
    assert _is_blocked_ip("240.0.0.1") is not None   # reserved
    assert _is_blocked_ip("224.0.0.1") is not None   # multicast
    assert _is_blocked_ip("0.0.0.0") is not None      # unspecified
    assert _is_blocked_ip("8.8.8.8") is None          # real public IP, not blocked


def test_is_blocked_ip_ipv6_loopback_and_link_local():
    assert _is_blocked_ip("::1") is not None
    assert _is_blocked_ip("fe80::1") is not None


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
