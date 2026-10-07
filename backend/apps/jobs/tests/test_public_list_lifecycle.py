"""Regression coverage for the public job list endpoint's lifecycle gating.

Investigated as part of the "fix the known backend test failure" directive:
`tests/integration/test_features.py::TestJobListEndpoint::test_archived_jobs_excluded`
was failing — but NOT because of a production bug. `JobListView.get_queryset()`
(apps/jobs/views.py) already correctly gates on the authoritative
`Job.objects.visible()` queryset (quality_state-based), per the documented,
intentional decision in `test_quality_state.py::TestStaleStatusCannotExcludeValidJobs`
that `Job.status` alone must NOT be trusted for visibility (it's write-once
and can go stale after verification). The failing test's `inactive_job`
fixture (tests/conftest.py) only set `status="archived"` without also
setting `quality_state="archived"` — a state the real archival action
(`JobDetailView.destroy()`) never actually produces (it always sets BOTH
fields together). The fixture was stale, not the endpoint.

Fix applied: the `inactive_job` fixture now sets `quality_state="archived"`
to match the real archival shape. These tests pin the correct business
rule across the full lifecycle matrix so this doesn't regress silently
again, and so a future "is X done" check doesn't have to re-derive the
rule from scratch.

Business rule (confirmed against JobQuerySet.visible()/.active(), the
Job Quality Engine's 9-state model, and JobDetailView.destroy()):
  - Public job list = Job.objects.visible().exclude(is_expired=True)
  - visible() states: active, probably_active, direct_verified,
    needs_verification
  - NOT visible: expired, archived, broken, duplicate, rejected
  - `status` (the legacy field) is NOT consulted for visibility at all —
    only `quality_state` + `is_expired` are authoritative.
"""
import datetime

import pytest
from rest_framework import status as http_status

from apps.jobs.models import Job

PUBLIC_LIST_URL = "/api/v1/jobs/"


def _make_job(company, source, quality_state, slug, **extra):
    defaults = dict(
        title="Lifecycle Test Job",
        slug=slug,
        company=company,
        source=source,
        location="Remote",
        location_type="remote",
        industry="technology",
        experience_level="mid",
        description="Lifecycle coverage.",
        source_url=f"https://testboard.example.com/jobs/{slug}",
        posted_at=datetime.date.today(),
        quality_state=quality_state,
    )
    defaults.update(extra)
    return Job.objects.create(**defaults)


@pytest.mark.django_db
class TestPublicJobListLifecycleGating:
    """Every quality_state, checked against whether it appears in the
    public /api/v1/jobs/ list — the single source of truth is
    Job.QUALITY_VISIBLE_STATES, not an ad hoc per-test guess."""

    @pytest.mark.parametrize(
        "quality_state,should_be_visible",
        [
            ("active", True),
            ("probably_active", True),
            ("direct_verified", True),
            ("needs_verification", True),
            ("expired", False),
            ("archived", False),
            ("broken", False),
            ("duplicate", False),
            ("rejected", False),
        ],
    )
    def test_quality_state_visibility_matches_canonical_set(
        self, api_client, company, source, quality_state, should_be_visible
    ):
        job = _make_job(company, source, quality_state, f"lifecycle-{quality_state}")
        resp = api_client.get(PUBLIC_LIST_URL)
        assert resp.status_code == http_status.HTTP_200_OK
        slugs = {j["slug"] for j in resp.json()["data"]["results"]}
        if should_be_visible:
            assert job.slug in slugs, f"quality_state={quality_state} should be publicly visible"
        else:
            assert job.slug not in slugs, f"quality_state={quality_state} should NOT be publicly visible"

    def test_archived_via_real_destroy_action_is_excluded(self, api_client, admin_client, job):
        """End-to-end: use the real DELETE action (not a hand-built fixture)
        and confirm the archived job disappears from the public list,
        proving the destroy()->archive path and the list gate agree."""
        resp = api_client.get(PUBLIC_LIST_URL)
        assert job.slug in {j["slug"] for j in resp.json()["data"]["results"]}

        del_resp = admin_client.delete(f"{PUBLIC_LIST_URL}{job.slug}/")
        assert del_resp.status_code == http_status.HTTP_200_OK

        job.refresh_from_db()
        assert job.status == "archived"
        assert job.quality_state == "archived"

        resp2 = api_client.get(PUBLIC_LIST_URL)
        assert job.slug not in {j["slug"] for j in resp2.json()["data"]["results"]}

    def test_expired_flag_excludes_regardless_of_quality_state(self, api_client, company, source):
        """is_expired=True must exclude a job even if quality_state alone
        would otherwise mark it visible (defensive: the two signals are
        ANDed by the queryset, not OR'd)."""
        job = _make_job(
            company, source, "active", "lifecycle-expired-flag", is_expired=True
        )
        resp = api_client.get(PUBLIC_LIST_URL)
        assert resp.status_code == http_status.HTTP_200_OK
        slugs = {j["slug"] for j in resp.json()["data"]["results"]}
        assert job.slug not in slugs

    def test_stale_rejected_status_does_not_hide_a_healthy_job(
        self, api_client, company, source
    ):
        """Documented intentional behavior (test_quality_state.py): a job
        with a stale status='rejected' but a healthy quality_state must
        still be publicly visible. Re-asserted here at the HTTP layer, not
        just the queryset layer, to lock in the end-to-end contract."""
        job = _make_job(
            company, source, "probably_active", "lifecycle-stale-status",
            status="rejected",
        )
        resp = api_client.get(PUBLIC_LIST_URL)
        slugs = {j["slug"] for j in resp.json()["data"]["results"]}
        assert job.slug in slugs
