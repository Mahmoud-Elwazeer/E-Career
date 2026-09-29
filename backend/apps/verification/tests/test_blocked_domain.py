"""Tests for the aggregator-rejection moat: is_blocked_domain matching.

The direct-apply moat is a NON-NEGOTIABLE product rule: apply URLs on
aggregators (LinkedIn/Indeed/ZipRecruiter/Monster/etc.) must be rejected,
only genuine employer/ATS destinations accepted. Previously the matcher used
naive substring matching (``any(b in domain for b in blocked)``) which both
over-matched (a blocked ``indeed.com`` would flag ``notindeed.com``) and could
be bypassed. These tests pin correct dot-boundary suffix matching.
"""
from django.test import TestCase

from apps.verification import models as vmodels
from apps.verification.models import (
    BlockedDomain,
    is_blocked_domain,
    _normalize_host,
)


class NormalizeHostTests(TestCase):
    def test_strips_scheme_path_port_and_www(self):
        self.assertEqual(_normalize_host("https://www.indeed.com/jobs/x"), "indeed.com")
        self.assertEqual(_normalize_host("http://apply.indeed.com:443/apply"), "apply.indeed.com")
        self.assertEqual(_normalize_host("LinkedIn.com"), "linkedin.com")
        self.assertEqual(_normalize_host("user@host.example.com"), "host.example.com")
        self.assertEqual(_normalize_host(""), "")


class IsBlockedDomainTests(TestCase):
    def setUp(self):
        # These may already be seeded by migration 0003; ensure present + active.
        for d in ("indeed.com", "linkedin.com", "ziprecruiter.com"):
            BlockedDomain.objects.update_or_create(
                domain=d, defaults={"reason": "aggregator", "is_active": True}
            )
        # Reset the module-level cache so DB rows here are seen.
        vmodels._blocked_cache = None
        vmodels._blocked_cache_ts = 0

    def test_exact_host_blocked(self):
        self.assertTrue(is_blocked_domain("indeed.com"))
        self.assertTrue(is_blocked_domain("linkedin.com"))

    def test_subdomain_blocked(self):
        self.assertTrue(is_blocked_domain("apply.indeed.com"))
        self.assertTrue(is_blocked_domain("www.linkedin.com"))
        self.assertTrue(is_blocked_domain("careers.ziprecruiter.com"))

    def test_full_url_blocked(self):
        self.assertTrue(is_blocked_domain("https://apply.indeed.com/apply/123"))

    def test_lookalike_not_blocked(self):
        # These would be FALSE POSITIVES under the old substring matcher.
        self.assertFalse(is_blocked_domain("notindeed.com"))
        self.assertFalse(is_blocked_domain("myindeed.com.employer-ats.io"))
        self.assertFalse(is_blocked_domain("mylinkedin.com"))

    def test_genuine_ats_not_blocked(self):
        self.assertFalse(is_blocked_domain("boards.greenhouse.io"))
        self.assertFalse(is_blocked_domain("jobs.lever.co"))
        self.assertFalse(is_blocked_domain("careers.google.com"))

    def test_empty_input(self):
        self.assertFalse(is_blocked_domain(""))
