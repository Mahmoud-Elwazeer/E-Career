"""
Embedding Pipeline Stage

Generates Cohere Embed v3 vectors (1024d) and stores them via pgvector.
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and storing embeddings using the vector service (pgvector).
    """

    def __init__(self):
        self._vector_service = None

    @property
    def _vs(self):
        if self._vector_service is None:
            from apps.vectors.service import get_vector_service
            self._vector_service = get_vector_service()
        return self._vector_service

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        try:
            embeddings = self._vs.generate_embeddings([text], input_type="search_document")
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def store_embedding(self, job_id: str, text: str, metadata: Dict = None) -> bool:
        try:
            embedding = self.generate_embedding(text)
            if not embedding:
                return False

            from apps.vectors.plugins.vector_plugin import VectorPoint
            point = VectorPoint(id=job_id, vector=embedding, payload=metadata or {})
            self._vs.vector_plugin.upsert("jobs", [point])
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding for job {job_id}: {e}")
            return False

    def batch_store_embeddings(self, jobs_data: List[Dict]) -> Dict[str, int]:
        success = 0
        failed = 0
        for job_data in jobs_data:
            job_id = str(job_data.get('id', ''))
            text = job_data.get('text', '')
            if self.store_embedding(job_id, text, job_data.get('metadata')):
                success += 1
            else:
                failed += 1
        return {'success': success, 'failed': failed}

    def search_by_embedding(self, query: str, limit: int = 10) -> List[Dict]:
        try:
            response = self._vs.semantic_search("jobs", query, limit=limit)
            return [
                {'job_id': r.id, 'score': r.score, 'text': r.payload.get('text', '')}
                for r in response.results
            ]
        except Exception as e:
            logger.error(f"Failed to search by embedding: {e}")
            return []

    def delete_job_embedding(self, job_id: str) -> bool:
        try:
            self._vs.vector_plugin.delete("jobs", [job_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete embedding for job {job_id}: {e}")
            return False


embedding_service = EmbeddingService()


def generate_and_store_embedding(job_id: str, text: str, metadata: Dict = None) -> bool:
    return embedding_service.store_embedding(job_id, text, metadata)
