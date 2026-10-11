"""Regression test for ResearchEngine._semantic_job_search.

Found while auditing the RAG/knowledge layer for citation-readiness
(Open Glean evaluation follow-up). This method had TWO real bugs that
made it a no-op in production, always silently falling through to the
broad `except Exception: pass` below it:

  1. `from apps.vectors.service import vector_service` - that module has
     no module-level `vector_service` singleton, only `get_vector_service()`
     (a lazy factory) and a private `_vector_service`. This import always
     raised ImportError.
  2. Even past that, the code read `r.metadata` on each
     `VectorSearchResult`, but the dataclass's real field is `payload`
     (apps/vectors/plugins/vector_plugin.py) - this would have raised
     AttributeError on every result once bug #1 was fixed.

Both were invisible because `_gather_platform_context` wraps the whole
call in a broad `except Exception: pass` and silently falls back to an
ORM query instead - the research feature "worked" (never crashed) while
quietly never using semantic search at all.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.intelligence.research_engine import ResearchEngine
from apps.vectors.plugins.vector_plugin import VectorSearchResponse, VectorSearchResult


class SemanticJobSearchTests(TestCase):
    def setUp(self):
        self.engine = ResearchEngine()

    def test_imports_get_vector_service_not_a_nonexistent_singleton(self):
        """Guards against reintroducing `from apps.vectors.service import
        vector_service` (no such name exists in that module)."""
        import apps.vectors.service as vs

        self.assertFalse(hasattr(vs, "vector_service"))
        self.assertTrue(hasattr(vs, "get_vector_service"))

    @patch("apps.vectors.service.get_vector_service")
    def test_semantic_job_search_reads_payload_field_and_formats_results(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.semantic_search.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-1",
                    score=0.87,
                    payload={"title": "Senior Backend Engineer", "company": "Acme Corp"},
                ),
                VectorSearchResult(
                    id="job-2",
                    score=0.81,
                    payload={"title": "Backend Engineer II", "company": "Globex"},
                ),
            ],
            total=2,
            query_time_ms=12,
        )
        mock_get_service.return_value = mock_service

        result = self.engine._semantic_job_search("backend engineer")

        self.assertIn("Senior Backend Engineer", result)
        self.assertIn("Acme Corp", result)
        self.assertIn("0.87", result)
        self.assertIn("Semantically related jobs (2):", result)
        mock_service.semantic_search.assert_called_once()
        call_kwargs = mock_service.semantic_search.call_args.kwargs
        self.assertEqual(call_kwargs["collection"], "jobs")

    @patch("apps.vectors.service.get_vector_service")
    def test_semantic_job_search_returns_empty_string_on_no_results(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.semantic_search.return_value = VectorSearchResponse(
            results=[], total=0, query_time_ms=5
        )
        mock_get_service.return_value = mock_service

        result = self.engine._semantic_job_search("a query with no matches")
        self.assertEqual(result, "")

    @patch("apps.vectors.service.get_vector_service", side_effect=Exception("vector db down"))
    def test_semantic_job_search_degrades_gracefully_on_failure(self, mock_get_service):
        """Even with the bugs fixed, a genuine infra failure must still
        degrade to an empty string, not propagate - _gather_platform_context
        falls back to an ORM query in that case."""
        result = self.engine._semantic_job_search("anything")
        self.assertEqual(result, "")
