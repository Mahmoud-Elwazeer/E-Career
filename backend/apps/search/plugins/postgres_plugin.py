from __future__ import annotations

import structlog
from django.db.models import Q, Value, FloatField
from django.db.models.functions import Greatest
from typing import Any

from .base import (
    FacetCount,
    SearchPlugin,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = structlog.get_logger()


class PostgresSearchPlugin(SearchPlugin):
    """PostgreSQL LIKE/icontains fallback when Typesense is unavailable."""

    def initialize(self) -> None:
        pass

    def search(self, collection: str, query: SearchQuery) -> SearchResponse:
        from apps.jobs.models import Job

        if collection != "jobs":
            return SearchResponse(hits=[], total=0, page=query.page, per_page=query.per_page)

        qs = Job.objects.select_related("company", "source").filter(
            status="active", is_expired=False
        )

        if query.q and query.q != "*":
            qs = qs.filter(
                Q(title__icontains=query.q)
                | Q(description__icontains=query.q)
                | Q(company__name__icontains=query.q)
            )

        qs = self._apply_filters(qs, query.filters)

        offset = (query.page - 1) * query.per_page
        total = qs.count()
        results = qs[offset : offset + query.per_page]

        hits = []
        for job in results:
            hits.append(SearchResult(
                id=str(job.id),
                score=1.0,
                data=self._job_to_dict(job),
            ))

        facets = self._compute_facets(qs, query.facets) if query.facets else {}

        return SearchResponse(
            hits=hits,
            total=total,
            page=query.page,
            per_page=query.per_page,
            facets=facets,
        )

    def index_document(self, collection: str, document: dict[str, Any]) -> None:
        pass

    def index_documents_batch(
        self, collection: str, documents: list[dict[str, Any]]
    ) -> int:
        return 0

    def delete_document(self, collection: str, document_id: str) -> None:
        pass

    def create_collection(self, collection: str, schema: dict[str, Any]) -> None:
        pass

    def drop_collection(self, collection: str) -> None:
        pass

    def health_check(self) -> bool:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def autocomplete(
        self, collection: str, prefix: str, field: str, limit: int = 5
    ) -> list[str]:
        from apps.jobs.models import Job

        if field == "title":
            return list(
                Job.objects.filter(title__istartswith=prefix, status="active")
                .values_list("title", flat=True)
                .distinct()[:limit]
            )
        return []

    def _apply_filters(self, qs, filters: dict[str, Any]):
        for key, value in filters.items():
            if value is None:
                continue

            if key == "location_type" and value:
                if isinstance(value, list):
                    qs = qs.filter(location_type__in=value)
                else:
                    qs = qs.filter(location_type=value)
            elif key == "work_arrangement" and value:
                if isinstance(value, list):
                    qs = qs.filter(work_arrangement__in=value)
                else:
                    qs = qs.filter(work_arrangement=value)
            elif key == "experience_level" and value:
                if isinstance(value, list):
                    qs = qs.filter(experience_level__in=value)
                else:
                    qs = qs.filter(experience_level=value)
            elif key == "employment_type" and value:
                if isinstance(value, list):
                    qs = qs.filter(employment_type__in=value)
                else:
                    qs = qs.filter(employment_type=value)
            elif key == "salary_min" and value:
                qs = qs.filter(salary_min__gte=value)
            elif key == "salary_max" and value:
                qs = qs.filter(salary_max__lte=value)
            elif key == "location" and value:
                qs = qs.filter(location__icontains=value)
            elif key == "company_name" and value:
                qs = qs.filter(company__name__icontains=value)
            elif key == "trust_score" and value:
                if isinstance(value, tuple):
                    low, high = value
                    if low is not None:
                        qs = qs.filter(legitimacy_score__gte=low)
                    if high is not None:
                        qs = qs.filter(legitimacy_score__lte=high)
                else:
                    qs = qs.filter(legitimacy_score__gte=value)

        return qs

    def _compute_facets(self, qs, facet_fields: list[str]) -> dict[str, list[FacetCount]]:
        facets = {}
        for field_name in facet_fields:
            if field_name in ("location_type", "work_arrangement", "experience_level", "employment_type"):
                counts = (
                    qs.exclude(**{f"{field_name}__isnull": True})
                    .exclude(**{field_name: ""})
                    .values_list(field_name, flat=True)
                )
                value_counts: dict[str, int] = {}
                for val in counts:
                    value_counts[val] = value_counts.get(val, 0) + 1
                facets[field_name] = [
                    FacetCount(value=k, count=v)
                    for k, v in sorted(value_counts.items(), key=lambda x: -x[1])
                ]
        return facets

    def _job_to_dict(self, job) -> dict[str, Any]:
        return {
            "id": str(job.id),
            "title": job.title,
            "slug": job.slug,
            "company_name": job.company.name if job.company else "",
            "company_slug": job.company.slug if job.company else "",
            "company_logo_url": job.company.logo_url if job.company else "",
            "location": job.location,
            "location_type": job.location_type,
            "work_arrangement": job.work_arrangement or "",
            "experience_level": job.experience_level,
            "employment_type": job.employment_type or "",
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "direct_apply_url": job.direct_apply_url,
            "source_url": job.source_url,
            "posted_at": str(job.posted_at) if job.posted_at else "",
            "trust_score": job.legitimacy_score,
        }
