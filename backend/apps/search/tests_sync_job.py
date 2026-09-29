"""Regression test for the SearchService.sync_job contract used by signals.

Guards the production bug where every ingested job logged
"'SearchService' object has no attribute 'sync_job'" — jobs saved but never
indexed (not searchable). The post_save signal calls search_service.sync_job(job),
so that method must exist and accept a Job-like object.
"""
import inspect
from types import SimpleNamespace
from unittest.mock import patch

from apps.search.service import SearchService


def test_searchservice_has_sync_job():
    assert hasattr(SearchService, "sync_job")
    sig = inspect.signature(SearchService.sync_job)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    assert len(params) == 1  # sync_job(job)


def test_sync_job_serializes_and_indexes():
    svc = SearchService()
    captured = {}

    def fake_index(document):
        captured["doc"] = document

    # Minimal Job-like object matching job_to_search_document's reads.
    job = SimpleNamespace(
        id=123, title="Engineer", slug="engineer-123",
        description="x", company=SimpleNamespace(name="Acme", slug="acme", logo_url=""),
        location="Cairo", location_type="onsite", experience_level="senior",
        source_url="", posted_at=None, work_arrangement="onsite",
        employment_type="full_time", salary_min=None, salary_max=None,
        salary_currency="USD", direct_apply_url="https://boards.greenhouse.io/acme/jobs/1",
        legitimacy_score=0.5, industry="technology", ats_platform="greenhouse",
    )
    job.tags = SimpleNamespace(values_list=lambda *a, **k: [])

    with patch.object(svc, "index_job", side_effect=fake_index):
        svc.sync_job(job)

    assert captured["doc"]["id"] == "123"
    assert captured["doc"]["trust_score"] == 0.5  # feeds mandatory trust filter
    assert captured["doc"]["direct_apply_url"].startswith("https://boards.greenhouse.io")
