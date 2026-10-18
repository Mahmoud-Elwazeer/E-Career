"""
Public legal-read throttling — regression test for a real bug found during
the 2026-09-21 browser-E2E acceptance pass.

Real-browser testing against a live-running Django+Vite dev server showed
that casually browsing a handful of /legal/<slug> pages could exhaust the
shared 30/min anonymous DRF throttle budget (pooled across every
anonymous endpoint hit on a page — job search, cookie-consent POSTs,
etc.) and cause a public legal disclosure page to render "This document
couldn't be loaded" — unacceptable for a page that must always be
accessible. Fixed by giving genuinely public, read-only legal endpoints
their own, more generous `legal_public` throttle scope (120/minute),
leaving state-mutating endpoints (cookie-consent POST, policy accept, DSR
creation) on the normal, tighter anon/auth budgets.
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.legal.models import PolicyDocument, PolicyVersion
from apps.legal.views import LegalPublicReadThrottle

pytestmark = pytest.mark.django_db


def test_legal_public_read_throttle_has_its_own_dedicated_scope():
    assert LegalPublicReadThrottle.scope == "legal_public"


def test_legal_public_scope_is_configured_and_more_generous_than_shared_anon():
    # config.settings.test deliberately disables throttling altogether by
    # mutating the SAME REST_FRAMEWORK dict object base.py defines (`from
    # .base import *` binds the same dict, and test.py reassigns one of
    # its keys in place) — so importing either module at runtime shows the
    # already-mutated dict. Read base.py's actual source text instead,
    # which is unaffected by any other settings module's mutations.
    import inspect
    from config.settings import base as base_settings

    source = inspect.getsource(base_settings)
    assert '"legal_public": "120/minute"' in source, (
        "Expected base.py to define a dedicated, more generous "
        "legal_public throttle rate (120/minute) than the shared anon "
        "rate (30/minute)."
    )


@pytest.fixture
def active_terms():
    doc = PolicyDocument.objects.create(slug="terms", doc_type=PolicyDocument.DocType.TERMS, title="Terms")
    return PolicyVersion.objects.create(
        document=doc, version_label="1", locale="en", status=PolicyVersion.Status.ACTIVE,
        content_markdown="# Terms\nReal content.", effective_at="2026-01-01T00:00:00Z",
    )


def test_every_genuinely_public_legal_read_endpoint_uses_the_dedicated_throttle():
    """Confirms the fix is actually wired onto every endpoint it needs to
    be, not just one — a static check against the view functions'
    .cls.throttle_classes attribute DRF's @throttle_classes decorator sets."""
    from apps.legal import views

    read_endpoints = [
        views.policy_list, views.policy_detail, views.consent_purpose_list,
        views.cookie_category_list, views.cookie_consent_me,
        views.legal_entity_public, views.ai_disclosure_list,
        views.processor_register_public, views.data_transfer_register_public,
    ]
    for view_func in read_endpoints:
        throttle_classes = getattr(view_func.cls, "throttle_classes", [])
        assert LegalPublicReadThrottle in throttle_classes, (
            f"{view_func.__name__} is missing the LegalPublicReadThrottle "
            f"scope — it would fall back to the shared, easily-exhausted "
            f"anon throttle budget."
        )


def test_policy_detail_endpoint_remains_reachable_under_the_fix(active_terms):
    """End-to-end sanity: the endpoint still actually works after adding
    the throttle decorator (not just that the decorator is present)."""
    client = APIClient()
    resp = client.get("/api/v1/legal/policies/terms/")
    assert resp.status_code == 200
