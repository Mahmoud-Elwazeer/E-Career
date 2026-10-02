from __future__ import annotations

import threading
import time

import structlog
from django.conf import settings

from .plugins.base import SearchPlugin, SearchQuery, SearchResponse
from .plugins.typesense_plugin import TypesenseSearchPlugin
from .plugins.postgres_plugin import PostgresSearchPlugin

logger = structlog.get_logger()

# Circuit breaker for index_job(): during a bulk ingestion run (e.g. a Lever/
# Ashby/Greenhouse source with hundreds of jobs), a single bad TYPESENSE_API_KEY
# previously caused one live HTTP call + two ERROR log lines PER JOB, every
# job, for the whole run (confirmed live: 833 jobs from openai-ashby alone).
# This doesn't change behavior (jobs still fall back correctly, search is
# unaffected since search_jobs already health-checks before querying) — it
# just stops hammering an endpoint already known to be down this run, and
# collapses the log spam to one WARNING per open/close transition instead of
# one ERROR pair per job. Class-level (not instance-level) because callers
# create a fresh SearchService() per job (see orchestrator._process_jobs).
_INDEX_CIRCUIT_LOCK = threading.Lock()
_INDEX_CIRCUIT_FAILURES = 0
_INDEX_CIRCUIT_OPEN_UNTIL = 0.0
_INDEX_CIRCUIT_FAILURE_THRESHOLD = 3
_INDEX_CIRCUIT_COOLDOWN_SECONDS = 300

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
        try:
            return plugin.search(JOBS_COLLECTION, query)
        except Exception as e:
            # Resilience: health_check may pass while the actual query fails
            # (e.g. Typesense 401 on a misconfigured API key). Never hard-crash
            # search — fall back to Postgres so results keep flowing. The
            # mandatory trust filter is already applied above.
            if plugin is not self.fallback:
                logger.warning(
                    "search_primary_failed_falling_back",
                    error=str(e), backend=type(plugin).__name__,
                )
                try:
                    return self.fallback.search(JOBS_COLLECTION, query)
                except Exception as fe:
                    logger.error("search_fallback_also_failed", error=str(fe))
                    raise
            raise

    def index_job(self, document: dict) -> bool:
        """Index one job document. Returns True only on confirmed success -
        callers (sync_job, signals) must not report success unless this
        returns True. Never raises - failures are logged and reflected only
        in the return value."""
        global _INDEX_CIRCUIT_FAILURES, _INDEX_CIRCUIT_OPEN_UNTIL

        now = time.monotonic()
        if now < _INDEX_CIRCUIT_OPEN_UNTIL:
            # Breaker open: skip the live call entirely during a known outage
            # window instead of repeating it for every job in the run.
            return False

        try:
            self.primary.index_document(JOBS_COLLECTION, document)
            with _INDEX_CIRCUIT_LOCK:
                _INDEX_CIRCUIT_FAILURES = 0
            return True
        except Exception as e:
            logger.error("search_index_job_failed", error=str(e), doc_id=document.get("id"))
            with _INDEX_CIRCUIT_LOCK:
                _INDEX_CIRCUIT_FAILURES += 1
                if _INDEX_CIRCUIT_FAILURES >= _INDEX_CIRCUIT_FAILURE_THRESHOLD:
                    _INDEX_CIRCUIT_OPEN_UNTIL = now + _INDEX_CIRCUIT_COOLDOWN_SECONDS
                    logger.warning(
                        "search_index_circuit_open",
                        reason=str(e),
                        cooldown_seconds=_INDEX_CIRCUIT_COOLDOWN_SECONDS,
                        note="skipping further index_job calls for this window; "
                             "jobs remain saved to DB, just not indexed to Typesense "
                             "until the breaker closes or the API key is fixed",
                    )
            return False

    def index_jobs_batch(self, documents: list[dict]) -> int:
        try:
            return self.primary.index_documents_batch(JOBS_COLLECTION, documents)
        except Exception as e:
            logger.error("search_batch_index_failed", error=str(e), count=len(documents))
            return 0

    def sync_job(self, job) -> bool:
        """Serialize a Job model to a search document and index it.

        Convenience used by the post_save signal (apps.search.signals) and the
        orchestrator's per-job ingestion step. Returns True only if the
        document was actually confirmed indexed - callers must not log/count
        success otherwise. Reuses the canonical document builder so search
        fields stay consistent with the schema.
        """
        from apps.search.document import job_to_search_document
        document = job_to_search_document(job)
        return self.index_job(document)

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
