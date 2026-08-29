"""
import json
PgVector Plugin

Fallback implementation of VectorPlugin using PostgreSQL with pgvector extension.
Canonical vector store for the platform.
"""

import time
import json
import structlog
from typing import List, Optional
from django.db import connection

from .vector_plugin import (
    VectorPlugin,
    VectorDocument,
    VectorSearchQuery,
    VectorSearchResult,
    VectorSearchResponse,
)

logger = structlog.get_logger(__name__)


class PgVectorPlugin(VectorPlugin):
    """PostgreSQL pgvector fallback implementation of VectorPlugin."""

    def __init__(self):
        self._ensure_extension()

    def _ensure_extension(self):
        """Ensure pgvector extension is installed."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as e:
            logger.warning("pgvector_extension_failed", error=str(e))

    def _table_name(self, collection: str) -> str:
        """Get table name for collection."""
        return f"vectors_{collection}"

    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "cosine",
    ) -> bool:
        """Create a pgvector table."""
        try:
            table_name = self._table_name(name)

            with connection.cursor() as cursor:
                # Create table
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id VARCHAR(255) PRIMARY KEY,
                        vector vector({vector_size}),
                        payload JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)

                # Create index based on distance metric
                if distance == "cosine":
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {table_name}_vector_cosine_idx
                        ON {table_name} USING ivfflat (vector vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                elif distance == "euclidean":
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {table_name}_vector_l2_idx
                        ON {table_name} USING ivfflat (vector vector_l2_ops)
                        WITH (lists = 100);
                    """)

            logger.info("pgvector_collection_created", collection=name, vector_size=vector_size)
            return True

        except Exception as e:
            logger.error("pgvector_create_collection_failed", collection=name, error=str(e))
            return False

    def delete_collection(self, name: str) -> bool:
        """Delete a pgvector table."""
        try:
            table_name = self._table_name(name)
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

            logger.info("pgvector_collection_deleted", collection=name)
            return True

        except Exception as e:
            logger.error("pgvector_delete_collection_failed", collection=name, error=str(e))
            return False

    def collection_exists(self, name: str) -> bool:
        """Check if pgvector table exists."""
        try:
            table_name = self._table_name(name)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, [table_name])
                return cursor.fetchone()[0]

        except Exception as e:
            logger.error("pgvector_collection_exists_failed", collection=name, error=str(e))
            return False

    def upsert(
        self,
        collection: str,
        documents: List[VectorDocument],
    ) -> int:
        """Upsert documents into pgvector table."""
        try:
            table_name = self._table_name(collection)

            with connection.cursor() as cursor:
                for doc in documents:
                    vector_str = "[" + ",".join(map(str, doc.vector)) + "]"
                    cursor.execute(f"""
                        INSERT INTO {table_name} (id, vector, payload)
                        VALUES (%s, %s::vector, %s::jsonb)
                        ON CONFLICT (id) DO UPDATE
                        SET vector = EXCLUDED.vector,
                            payload = EXCLUDED.payload;
                    """, [doc.id, vector_str, json.dumps(doc.payload)])

            logger.info("pgvector_upsert_success", collection=collection, count=len(documents))
            return len(documents)

        except Exception as e:
            logger.error("pgvector_upsert_failed", collection=collection, error=str(e))
            return 0

    def delete(
        self,
        collection: str,
        ids: List[str],
    ) -> int:
        """Delete documents from pgvector table."""
        try:
            table_name = self._table_name(collection)

            with connection.cursor() as cursor:
                cursor.execute(f"""
                    DELETE FROM {table_name}
                    WHERE id = ANY(%s);
                """, [ids])

            logger.info("pgvector_delete_success", collection=collection, count=len(ids))
            return len(ids)

        except Exception as e:
            logger.error("pgvector_delete_failed", collection=collection, error=str(e))
            return 0

    def search(
        self,
        collection: str,
        query: VectorSearchQuery,
    ) -> VectorSearchResponse:
        """Search for similar vectors in pgvector table."""
        start_time = time.time()

        try:
            table_name = self._table_name(collection)
            vector_str = "[" + ",".join(map(str, query.vector)) + "]"

            # Build WHERE clause from filters
            where_clauses = []
            params = [vector_str]

            if query.filter:
                for key, value in query.filter.items():
                    if isinstance(value, (int, float, str, bool)):
                        where_clauses.append(f"payload->>'{key}' = %s")
                        params.append(str(value))
                    elif isinstance(value, dict):
                        # Range filter
                        if "gte" in value:
                            where_clauses.append(f"(payload->>'{key}')::numeric >= %s")
                            params.append(value["gte"])
                        if "lte" in value:
                            where_clauses.append(f"(payload->>'{key}')::numeric <= %s")
                            params.append(value["lte"])

            where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

            with connection.cursor() as cursor:
                # Cosine similarity search
                # Params order: vector_str (for SELECT), filters, vector_str (for ORDER BY), limit
                final_params = params + [vector_str, query.limit]
                cursor.execute(f"""
                    SELECT id, payload, 1 - (vector <=> %s::vector) as score
                    FROM {table_name}
                    WHERE {where_sql}
                    ORDER BY vector <=> %s::vector
                    LIMIT %s;
                """, final_params)

                rows = cursor.fetchall()

                # Apply score threshold if specified
                results = []
                for row in rows:
                    doc_id, payload, score = row
                    if query.score_threshold is None or score >= query.score_threshold:
                        results.append(
                            VectorSearchResult(
                                id=doc_id,
                                score=score,
                                payload=json.loads(payload) if isinstance(payload, str) else (payload or {}),
                            )
                        )

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "pgvector_search_success",
                collection=collection,
                results=len(results),
                time_ms=query_time_ms,
            )

            return VectorSearchResponse(
                results=results,
                total=len(results),
                query_time_ms=query_time_ms,
            )

        except Exception as e:
            logger.error("pgvector_search_failed", collection=collection, error=str(e))
            return VectorSearchResponse(
                results=[],
                total=0,
                query_time_ms=int((time.time() - start_time) * 1000),
            )

    def get(
        self,
        collection: str,
        id: str,
    ) -> Optional[VectorDocument]:
        """Get a document by ID from pgvector table."""
        try:
            table_name = self._table_name(collection)

            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT id, vector::text, payload
                    FROM {table_name}
                    WHERE id = %s;
                """, [id])

                row = cursor.fetchone()
                if not row:
                    return None

                doc_id, vector_str, payload = row

                # Parse vector string to list of floats
                vector = [float(x) for x in vector_str.strip("[]").split(",")]

                return VectorDocument(
                    id=doc_id,
                    vector=vector,
                    payload=json.loads(payload) if isinstance(payload, str) else (payload or {}),
                )

        except Exception as e:
            logger.error("pgvector_get_failed", collection=collection, id=id, error=str(e))
            return None

    def count(self, collection: str) -> int:
        """Count documents in pgvector table."""
        try:
            table_name = self._table_name(collection)

            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                return cursor.fetchone()[0]

        except Exception as e:
            logger.error("pgvector_count_failed", collection=collection, error=str(e))
            return 0

    def health_check(self) -> dict:
        """Check pgvector health."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
                version = cursor.fetchone()

                return {
                    "healthy": version is not None,
                    "version": version[0] if version else None,
                    "backend": "pgvector",
                }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "backend": "pgvector",
            }
