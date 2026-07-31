from __future__ import annotations

import structlog
import typesense
from django.conf import settings
from typing import Any

from .base import (
    FacetCount,
    SearchPlugin,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = structlog.get_logger()


class TypesenseSearchPlugin(SearchPlugin):
    """Typesense implementation of the SearchPlugin interface."""

    def __init__(self):
        self._client: typesense.Client | None = None

    @property
    def client(self) -> typesense.Client:
        if self._client is None:
            self.initialize()
        return self._client

    def initialize(self) -> None:
        self._client = typesense.Client({
            "nodes": [{
                "host": settings.TYPESENSE_HOST,
                "port": settings.TYPESENSE_PORT,
                "protocol": settings.TYPESENSE_PROTOCOL,
            }],
            "api_key": settings.TYPESENSE_API_KEY,
            "connection_timeout_seconds": 5,
        })

    def search(self, collection: str, query: SearchQuery) -> SearchResponse:
        search_params = self._build_search_params(query)

        try:
            result = self.client.collections[collection].documents.search(
                search_params
            )
        except typesense.exceptions.ObjectNotFound:
            logger.warning("typesense_collection_not_found", collection=collection)
            return SearchResponse(hits=[], total=0, page=query.page, per_page=query.per_page)
        except Exception as e:
            logger.error("typesense_search_error", error=str(e), collection=collection)
            raise

        return self._parse_response(result, query)

    def index_document(self, collection: str, document: dict[str, Any]) -> None:
        try:
            self.client.collections[collection].documents.upsert(document)
        except Exception as e:
            logger.error(
                "typesense_index_error",
                error=str(e),
                collection=collection,
                doc_id=document.get("id"),
            )
            raise

    def index_documents_batch(
        self, collection: str, documents: list[dict[str, Any]]
    ) -> int:
        if not documents:
            return 0

        try:
            results = self.client.collections[collection].documents.import_(
                documents, {"action": "upsert"}
            )
            success_count = sum(1 for r in results if r.get("success", True))
            failures = [r for r in results if not r.get("success", True)]
            if failures:
                logger.warning(
                    "typesense_batch_partial_failure",
                    collection=collection,
                    total=len(documents),
                    failed=len(failures),
                )
            return success_count
        except Exception as e:
            logger.error("typesense_batch_error", error=str(e), collection=collection)
            raise

    def delete_document(self, collection: str, document_id: str) -> None:
        try:
            self.client.collections[collection].documents[document_id].delete()
        except typesense.exceptions.ObjectNotFound:
            pass
        except Exception as e:
            logger.error(
                "typesense_delete_error",
                error=str(e),
                collection=collection,
                doc_id=document_id,
            )
            raise

    def create_collection(self, collection: str, schema: dict[str, Any]) -> None:
        schema["name"] = collection
        try:
            self.client.collections.create(schema)
            logger.info("typesense_collection_created", collection=collection)
        except typesense.exceptions.ObjectAlreadyExists:
            logger.info("typesense_collection_exists", collection=collection)

    def drop_collection(self, collection: str) -> None:
        try:
            self.client.collections[collection].delete()
            logger.info("typesense_collection_dropped", collection=collection)
        except typesense.exceptions.ObjectNotFound:
            pass

    def health_check(self) -> bool:
        try:
            return self.client.operations.is_healthy()
        except Exception:
            return False

    def autocomplete(
        self, collection: str, prefix: str, field: str, limit: int = 5
    ) -> list[str]:
        try:
            result = self.client.collections[collection].documents.search({
                "q": prefix,
                "query_by": field,
                "prefix": "true",
                "per_page": limit,
            })
            return [
                hit["document"].get(field, "")
                for hit in result.get("hits", [])
            ]
        except Exception as e:
            logger.error("typesense_autocomplete_error", error=str(e))
            return []

    def _build_search_params(self, query: SearchQuery) -> dict[str, Any]:
        params: dict[str, Any] = {
            "q": query.q or "*",
            "query_by": ",".join(query.filters.pop("query_by", query.query_by or ["title", "description"])),
            "page": query.page,
            "per_page": query.per_page,
            "highlight_full_fields": "title",
            "num_typos": 2,
            "typo_tokens_threshold": 3,
        }

        if query.facets:
            params["facet_by"] = ",".join(query.facets)

        if query.sort_by:
            params["sort_by"] = query.sort_by

        filter_parts = self._build_filter_string(query.filters)
        if filter_parts:
            params["filter_by"] = " && ".join(filter_parts)

        return params

    def _build_filter_string(self, filters: dict[str, Any]) -> list[str]:
        parts = []
        for key, value in filters.items():
            if key == "query_by":
                continue
            if value is None:
                continue
            if isinstance(value, list):
                parts.append(f"{key}:[{','.join(str(v) for v in value)}]")
            elif isinstance(value, tuple) and len(value) == 2:
                low, high = value
                if low is not None and high is not None:
                    parts.append(f"{key}:[{low}..{high}]")
                elif low is not None:
                    parts.append(f"{key}:>={low}")
                elif high is not None:
                    parts.append(f"{key}:<={high}")
            elif isinstance(value, bool):
                parts.append(f"{key}:={'true' if value else 'false'}")
            else:
                parts.append(f"{key}:={value}")
        return parts

    def _parse_response(self, result: dict, query: SearchQuery) -> SearchResponse:
        hits = []
        for hit in result.get("hits", []):
            doc = hit.get("document", {})
            highlights = {}
            for hl in hit.get("highlights", []):
                field_name = hl.get("field", "")
                snippet = hl.get("snippet", "") or hl.get("value", "")
                if field_name and snippet:
                    highlights[field_name] = snippet

            hits.append(SearchResult(
                id=str(doc.get("id", "")),
                score=hit.get("text_match_info", {}).get("score", 0),
                data=doc,
                highlights=highlights,
            ))

        facets: dict[str, list[FacetCount]] = {}
        for facet in result.get("facet_counts", []):
            field_name = facet.get("field_name", "")
            counts = [
                FacetCount(value=c["value"], count=c["count"])
                for c in facet.get("counts", [])
            ]
            facets[field_name] = counts

        return SearchResponse(
            hits=hits,
            total=result.get("found", 0),
            page=query.page,
            per_page=query.per_page,
            facets=facets,
            query_time_ms=result.get("search_time_ms", 0),
        )
