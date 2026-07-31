from __future__ import annotations

import structlog
from django.conf import settings

from .plugins.base import SearchPlugin, SearchQuery, SearchResponse
from .plugins.typesense_plugin import TypesenseSearchPlugin
from .plugins.postgres_plugin import PostgresSearchPlugin

logger = structlog.get_logger()

JOBS_COLLECTION = "jobs"

JOBS_SCHEMA = {
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "slug", "type": "string", "index": False},
        {"name": "description", "type": "string"},
        {"name": "company_name", "type": "string", "facet": True},
        {"name": "company_slug", "type": "string", "index": False},
        {"name": "company_logo_url", "type": "string", "index": False, "optional": True},
        {"name": "location", "type": "string", "facet": True},
        {"name": "location_type", "type": "string", "facet": True},
        {"name": "work_arrangement", "type": "string", "facet": True, "optional": True},
        {"name": "experience_level", "type": "string", "facet": True},
        {"name": "employment_type", "type": "string", "facet": True, "optional": True},
        {"name": "salary_min", "type": "int32", "optional": True},
        {"name": "salary_max", "type": "int32", "optional": True},
        {"name": "salary_currency", "type": "string", "optional": True},
        {"name": "direct_apply_url", "type": "string", "index": False, "optional": True},
        {"name": "source_url", "type": "string", "index": False},
        {"name": "posted_at", "type": "string", "facet": True},
        {"name": "posted_at_timestamp", "type": "int64"},
        {"name": "trust_score", "type": "float", "facet": True, "optional": True},
        {"name": "tags", "type": "string[]", "facet": True, "optional": True},
        {"name": "industry", "type": "string", "facet": True, "optional": True},
        {"name": "ats_platform", "type": "string", "facet": True, "optional": True},
    ],
    "default_sorting_field": "posted_at_timestamp",
    "token_separators": ["-", "_"],
}


class SearchService:
    """Unified search service with automatic fallback."""

    def __init__(self):
        self._primary: SearchPlugin | None = None
        self._fallback: SearchPlugin | None = None

    @property
    def primary(self) -> SearchPlugin:
        if self._primary is None:
            self._primary = TypesenseSearchPlugin()
        return self._primary

    @property
    def fallback(self) -> SearchPlugin:
        if self._fallback is None:
            self._fallback = PostgresSearchPlugin()
        return self._fallback

    def _get_plugin(self) -> SearchPlugin:
        try:
            if self.primary.health_check():
                return self.primary
        except Exception:
            pass
        logger.warning("search_fallback_activated", reason="typesense_unavailable")
        return self.fallback

    def search_jobs(self, query: SearchQuery) -> SearchResponse:
        self._enforce_trust_score_filter(query)
        plugin = self._get_plugin()
        return plugin.search(JOBS_COLLECTION, query)

    def index_job(self, document: dict) -> None:
        try:
            self.primary.index_document(JOBS_COLLECTION, document)
        except Exception as e:
            logger.error("search_index_job_failed", error=str(e), doc_id=document.get("id"))

    def index_jobs_batch(self, documents: list[dict]) -> int:
        try:
            return self.primary.index_documents_batch(JOBS_COLLECTION, documents)
        except Exception as e:
            logger.error("search_batch_index_failed", error=str(e), count=len(documents))
            return 0

    def delete_job(self, job_id: str) -> None:
        try:
            self.primary.delete_document(JOBS_COLLECTION, job_id)
        except Exception as e:
            logger.error("search_delete_job_failed", error=str(e), job_id=job_id)

    def autocomplete_jobs(self, prefix: str, limit: int = 5) -> list[str]:
        plugin = self._get_plugin()
        return plugin.autocomplete(JOBS_COLLECTION, prefix, "title", limit)

    def ensure_collection(self) -> None:
        try:
            self.primary.create_collection(JOBS_COLLECTION, JOBS_SCHEMA)
        except Exception as e:
            logger.error("search_create_collection_failed", error=str(e))
            raise

    def recreate_collection(self) -> None:
        self.primary.drop_collection(JOBS_COLLECTION)
        self.primary.create_collection(JOBS_COLLECTION, JOBS_SCHEMA)

    def health_check(self) -> dict:
        primary_ok = False
        try:
            primary_ok = self.primary.health_check()
        except Exception:
            pass
        return {
            "typesense": "up" if primary_ok else "down",
            "fallback": "postgres",
        }

    def _enforce_trust_score_filter(self, query: SearchQuery) -> None:
        """NON-NEGOTIABLE: Every search MUST filter by trust_score threshold."""
        threshold = getattr(settings, "SEARCH_TRUST_SCORE_THRESHOLD", 0.4)
        if "trust_score" not in query.filters:
            query.filters["trust_score"] = (threshold, None)


_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
