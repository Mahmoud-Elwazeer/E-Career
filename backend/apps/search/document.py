from __future__ import annotations

import time
from datetime import datetime
from typing import Any


def job_to_search_document(job) -> dict[str, Any]:
    """Convert a Job model instance to a Typesense-ready document."""
    posted_timestamp = 0
    if job.posted_at:
        if isinstance(job.posted_at, datetime):
            posted_timestamp = int(job.posted_at.timestamp())
        else:
            posted_timestamp = int(
                datetime.combine(job.posted_at, datetime.min.time()).timestamp()
            )

    tags = []
    if hasattr(job, "prefetched_tags"):
        tags = job.prefetched_tags
    else:
        try:
            tags = list(job.tags.values_list("name", flat=True))
        except Exception:
            pass

    doc: dict[str, Any] = {
        "id": str(job.id),
        "title": job.title or "",
        "slug": job.slug or "",
        "description": (job.description or "")[:10000],
        "company_name": job.company.name if job.company else "",
        "company_slug": job.company.slug if job.company else "",
        "company_logo_url": job.company.logo_url if job.company else "",
        "location": job.location or "",
        "location_type": job.location_type or "",
        "experience_level": job.experience_level or "",
        "source_url": job.source_url or "",
        "posted_at": str(job.posted_at) if job.posted_at else "",
        "posted_at_timestamp": posted_timestamp,
    }

    if job.work_arrangement:
        doc["work_arrangement"] = job.work_arrangement
    if job.employment_type:
        doc["employment_type"] = job.employment_type
    if job.salary_min is not None:
        doc["salary_min"] = job.salary_min
    if job.salary_max is not None:
        doc["salary_max"] = job.salary_max
    if job.salary_currency:
        doc["salary_currency"] = job.salary_currency
    if job.direct_apply_url:
        doc["direct_apply_url"] = job.direct_apply_url
    if job.legitimacy_score is not None:
        doc["trust_score"] = job.legitimacy_score
    if tags:
        doc["tags"] = tags
    if job.industry:
        doc["industry"] = job.industry
    if job.ats_platform:
        doc["ats_platform"] = job.ats_platform

    return doc
