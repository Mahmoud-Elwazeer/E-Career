"""
Malware-scanning (ClamAV/pyclamd) tests — directive item 15.

Previously zero test coverage existed for apps/core/upload_security.py.
These tests mock pyclamd/clamd entirely (it is not actually installed in
this environment — confirmed: `import pyclamd` raises ModuleNotFoundError
here despite being pinned in requirements.txt, which is itself the exact
silent-degradation gap this item targets) so they exercise the REAL
decision logic in `_get_clamd_connection`/`scan_stream_for_malware`/
`scan_file_for_malware` without needing a live daemon.
"""
import io
import sys
import types
from unittest import mock

import pytest
from django.test import override_settings

from apps.core.upload_security import (
    scan_stream_for_malware, scan_file_for_malware, _get_clamd_connection,
)


def _install_fake_pyclamd(ping_ok=True, scan_result=None, raise_on_init=False):
    """Install a fake `pyclamd` module into sys.modules so
    `_get_clamd_connection`'s `import pyclamd` succeeds and returns a
    controllable fake daemon connection."""
    fake_module = types.ModuleType("pyclamd")

    class _FakeDaemon:
        def ping(self):
            if not ping_ok:
                raise ConnectionError("no ping response")
            return True

        def scan_stream(self, content):
            return scan_result

        def scan_file(self, path):
            return scan_result

    def _ctor(*args, **kwargs):
        if raise_on_init:
            raise ConnectionError("socket connect failed")
        return _FakeDaemon()

    fake_module.ClamdUnixSocket = _ctor
    fake_module.ClamdNetworkSocket = _ctor
    sys.modules["pyclamd"] = fake_module
    return fake_module


@pytest.fixture(autouse=True)
def _cleanup_fake_pyclamd():
    yield
    sys.modules.pop("pyclamd", None)


# ── pyclamd not installed at all ─────────────────────────────────────────────

def test_get_clamd_connection_returns_none_when_pyclamd_not_installed():
    sys.modules.pop("pyclamd", None)
    with mock.patch.dict(sys.modules, {"pyclamd": None}):
        cd, err = _get_clamd_connection()
    assert cd is None
    assert "not installed" in err


@override_settings(CLAMAV_FAIL_CLOSED=True)
def test_scan_stream_rejects_when_pyclamd_not_installed_and_fail_closed():
    with mock.patch.dict(sys.modules, {"pyclamd": None}):
        result = scan_stream_for_malware(io.BytesIO(b"hello"))
    assert result.clean is False
    assert "not installed" in result.error


@override_settings(CLAMAV_FAIL_CLOSED=False)
def test_scan_stream_accepts_unscanned_when_pyclamd_not_installed_and_fail_open():
    with mock.patch.dict(sys.modules, {"pyclamd": None}):
        result = scan_stream_for_malware(io.BytesIO(b"hello"))
    assert result.clean is True


# ── daemon unreachable ────────────────────────────────────────────────────────

@override_settings(CLAMAV_FAIL_CLOSED=True)
def test_scan_stream_rejects_when_daemon_unreachable_and_fail_closed():
    _install_fake_pyclamd(ping_ok=False)
    result = scan_stream_for_malware(io.BytesIO(b"hello"))
    assert result.clean is False
    assert "unreachable" in result.error


@override_settings(CLAMAV_FAIL_CLOSED=False)
def test_scan_stream_accepts_unscanned_when_daemon_unreachable_and_fail_open():
    _install_fake_pyclamd(ping_ok=False)
    result = scan_stream_for_malware(io.BytesIO(b"hello"))
    assert result.clean is True


# ── daemon reachable: clean vs infected ──────────────────────────────────────

def test_scan_stream_clean_file():
    _install_fake_pyclamd(ping_ok=True, scan_result=None)
    result = scan_stream_for_malware(io.BytesIO(b"a clean pdf-ish payload"))
    assert result.clean is True
    assert result.threat == ""


def test_scan_stream_detects_threat():
    _install_fake_pyclamd(ping_ok=True, scan_result={"stream": ("FOUND", "Eicar-Test-Signature")})
    result = scan_stream_for_malware(io.BytesIO(b"fake eicar content"))
    assert result.clean is False
    assert result.threat == "Eicar-Test-Signature"


def test_scan_stream_resets_file_position_after_scanning():
    _install_fake_pyclamd(ping_ok=True, scan_result=None)
    stream = io.BytesIO(b"some file content")
    stream.seek(5)
    scan_stream_for_malware(stream)
    assert stream.tell() == 5  # position restored, not left at EOF


def test_scan_file_clean():
    _install_fake_pyclamd(ping_ok=True, scan_result=None)
    result = scan_file_for_malware("/tmp/fake-clean.pdf")
    assert result.clean is True


def test_scan_file_detects_threat():
    _install_fake_pyclamd(
        ping_ok=True,
        scan_result={"/tmp/fake-infected.pdf": ("FOUND", "Win.Test.EICAR_HDB-1")},
    )
    result = scan_file_for_malware("/tmp/fake-infected.pdf")
    assert result.clean is False
    assert result.threat == "Win.Test.EICAR_HDB-1"


# ── connection construction errors ───────────────────────────────────────────

def test_get_clamd_connection_handles_socket_connect_failure():
    _install_fake_pyclamd(raise_on_init=True)
    cd, err = _get_clamd_connection()
    assert cd is None
    assert "unreachable" in err


# ── SystemHealthView malware-scanner check (directive item 15) ──────────────

@pytest.mark.django_db
class TestSystemHealthMalwareScannerCheck:
    """Confirms the previously-unmonitored ClamAV availability is now
    surfaced in the admin SystemHealthView."""

    def _admin_client(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        User = get_user_model()
        admin = User.objects.create_user(email="health-admin@test.com", password="pw12345x", role="admin")
        client = APIClient()
        client.force_authenticate(user=admin)
        return client

    @staticmethod
    def _unwrap(resp):
        body = resp.json()
        return body["data"] if "data" in body else body

    def test_reports_healthy_when_clamd_reachable(self):
        _install_fake_pyclamd(ping_ok=True, scan_result=None)
        client = self._admin_client()
        resp = client.get("/api/v1/admin-api/system-health/")
        assert resp.status_code == 200, resp.content
        data = self._unwrap(resp)
        checks = {c["name"]: c for c in data["checks"]}
        assert "Malware Scanner (ClamAV)" in checks
        assert checks["Malware Scanner (ClamAV)"]["status"] == "healthy"

    @override_settings(CLAMAV_FAIL_CLOSED=True)
    def test_reports_error_when_unreachable_and_fail_closed(self):
        with mock.patch.dict(sys.modules, {"pyclamd": None}):
            client = self._admin_client()
            resp = client.get("/api/v1/admin-api/system-health/")
        data = self._unwrap(resp)
        checks = {c["name"]: c for c in data["checks"]}
        assert checks["Malware Scanner (ClamAV)"]["status"] == "error"
        assert data["overall_status"] == "error"

    @override_settings(CLAMAV_FAIL_CLOSED=False)
    def test_reports_warning_when_unreachable_and_fail_open(self):
        with mock.patch.dict(sys.modules, {"pyclamd": None}):
            client = self._admin_client()
            resp = client.get("/api/v1/admin-api/system-health/")
        data = self._unwrap(resp)
        checks = {c["name"]: c for c in data["checks"]}
        assert checks["Malware Scanner (ClamAV)"]["status"] == "warning"
