"""
Tests for SSRF protection in safe_fetch.

Verifies that requests to private/loopback/link-local/metadata IPs are blocked.
"""
import pytest
from apps.core.safe_fetch import (
    safe_fetch,
    verify_url_is_live,
    SSRFBlockedError,
    _resolve_and_validate,
)


class TestSSRFProtection:
    """Test that SSRF attacks are blocked."""

    def test_blocks_localhost(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("localhost", "http://localhost/")
        assert "Loopback" in exc_info.value.reason or "Private" in exc_info.value.reason

    def test_blocks_127_0_0_1(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("127.0.0.1", "http://127.0.0.1/")
        assert "Loopback" in exc_info.value.reason or "Private" in exc_info.value.reason

    def test_blocks_metadata_endpoint(self):
        """Block AWS/GCP/Azure metadata endpoint 169.254.169.254."""
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("169.254.169.254", "http://169.254.169.254/")
        assert "blocked" in exc_info.value.reason.lower()

    def test_blocks_private_10_range(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("10.0.0.1", "http://10.0.0.1/")
        assert "Private" in exc_info.value.reason

    def test_blocks_private_192_168_range(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("192.168.1.1", "http://192.168.1.1/")
        assert "Private" in exc_info.value.reason

    def test_blocks_private_172_range(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            _resolve_and_validate("172.16.0.1", "http://172.16.0.1/")
        assert "Private" in exc_info.value.reason

    def test_verify_url_is_live_blocks_localhost(self):
        """verify_url_is_live returns (False, 0) for blocked URLs."""
        is_live, status = verify_url_is_live("http://localhost/admin")
        assert is_live is False
        assert status == 0

    def test_verify_url_is_live_blocks_metadata(self):
        is_live, status = verify_url_is_live("http://169.254.169.254/latest/meta-data/")
        assert is_live is False
        assert status == 0

    def test_verify_url_is_live_blocks_127(self):
        is_live, status = verify_url_is_live("http://127.0.0.1:6379/")
        assert is_live is False
        assert status == 0

    def test_safe_fetch_blocks_http_by_default(self):
        """Default mode blocks http:// scheme."""
        with pytest.raises(SSRFBlockedError) as exc_info:
            safe_fetch("http://example.com/", allow_http=False)
        assert "scheme" in exc_info.value.reason.lower()

    def test_safe_fetch_blocks_file_scheme(self):
        with pytest.raises(SSRFBlockedError) as exc_info:
            safe_fetch("file:///etc/passwd")
        assert "scheme" in exc_info.value.reason.lower()

    def test_safe_fetch_blocks_no_hostname(self):
        with pytest.raises(SSRFBlockedError):
            safe_fetch("https:///path/only")
