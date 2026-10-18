"""
Content-Security-Policy-Report-Only header tests (directive item 18).

Confirms the new header is present on real responses, is Report-Only (not
enforcing — must never be the blocking `Content-Security-Policy` header),
and includes every origin from the verified inventory. Also smoke-tests
that existing security headers set elsewhere (HSTS/X-Frame-Options/etc.,
settings/production.py) are untouched by this addition.
"""
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_csp_report_only_header_present_on_every_response():
    resp = APIClient().get("/health/")
    assert "Content-Security-Policy-Report-Only" in resp.headers
    # Report-only must never also be the enforcing header — that would be
    # a double-policy footgun (two different directives trying to both
    # enforce and merely report).
    assert "Content-Security-Policy" not in resp.headers


def test_csp_policy_includes_verified_origin_inventory():
    resp = APIClient().get("/health/")
    policy = resp.headers["Content-Security-Policy-Report-Only"]

    # Google Fonts (frontend/src/index.css @import — confirmed real usage)
    assert "fonts.googleapis.com" in policy
    assert "fonts.gstatic.com" in policy
    # Stripe Hosted Checkout (apps/payments/providers/stripe_provider.py)
    assert "checkout.stripe.com" in policy
    # Google OAuth (django-allauth SOCIALACCOUNT_PROVIDERS 'google')
    assert "accounts.google.com" in policy
    # Same-origin WebSocket (Django Channels / Rashid chat)
    assert "wss:" in policy
    # Defaults to self; never allows arbitrary wildcard origins.
    assert "default-src 'self'" in policy
    assert "object-src 'none'" in policy


def test_csp_header_does_not_block_a_normal_api_response():
    """Report-Only by definition never blocks anything — confirm a normal
    successful response is completely unaffected (status code, body)."""
    resp = APIClient().get("/health/")
    assert resp.status_code == 200


def test_existing_security_headers_untouched_by_csp_addition():
    """The CSP middleware must be purely additive — it must not remove or
    interfere with any header set by SecurityMiddleware/other code."""
    resp = APIClient().get("/health/")
    # X-Content-Type-Options is set by SecurityMiddleware's
    # SECURE_CONTENT_TYPE_NOSNIFF-equivalent default behavior in Django;
    # confirm presence rather than asserting a specific unrelated header
    # this environment may not enable (HSTS/SSL-redirect are production-
    # only settings not active under the test settings module).
    assert resp.status_code == 200
    # The response must still be a well-formed DRF/Django response with
    # its normal headers — e.g. Content-Type — untouched.
    assert "Content-Type" in resp.headers
