"""
Embedding Pipeline Stage

Generates Cohere Embed v3 vectors (1024d) and stores them in Qdrant.
"""
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and storing embeddings using Cohere and Qdrant.
    
    Features:
    - Generate Cohere Embed v3 vectors (1024 dimensions)
    - Store embeddings in Qdrant `jobs` collection
    - Support for batch processing
    """
    
    def __init__(self):
        self._qdrant_client = None
        self._cohere_client = None
        self._model_name = "embed-english-v3.0"
        self._embedding_dim = 1024
    
    @property
    def qdrant_client(self):
        """Lazy load Qdrant client"""
        if self._qdrant_client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import VectorParams, Distance, PointStruct
                
                qdrant_url = getattr(settings, 'QDRANT_URL', 'http://localhost:6333')
                self._qdrant_client = QdrantClient(url=qdrant_url)
                
                # Create collection if it doesn't exist
                self._ensure_collection_exists()
                
            except ImportError:
                logger.warning("Qdrant client not installed. Install with: pip install qdrant-client")
                self._qdrant_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant client: {e}")
                self._qdrant_client = None
        return self._qdrant_client
    
    @property
    def cohere_client(self):
        """Lazy load Cohere client"""
        if self._cohere_client is None:
            try:
                import cohere
                api_key = getattr(settings, 'COHERE_API_KEY', None)
                if api_key:
                    self._cohere_client = cohere.Client(api_key)
                else:
                    logger.warning("COHERE_API_KEY not set")
            except ImportError:
                logger.warning("Cohere client not installed. Install with: pip install cohere")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {e}")
        return self._cohere_client
    
    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists with correct configuration"""
        try:
            from qdrant_client.models import VectorParams, Distance, PointStruct
            
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            # Check if collection exists
            collections = self._qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                # Create collection with 1024-dimensional vectors
                self._qdrant_client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self._embedding_dim,
                        distance=Distance.COSINE,
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Cohere Embed v3.
        
        Args:
            text: Text to embed
            
        Returns:
            List of 1024 floats or None if generation failed
        """
        if not self.cohere_client:
            logger.warning("Cohere client not available")
            return None
        
        try:
            response = self.cohere_client.embed(
                texts=[text],
                model=self._model_name,
                input_type="search_document",
            )
            
            embeddings = response.embeddings
            if embeddings:
                return embeddings[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def store_embedding(self, job_id: str, text: str, metadata: Dict = None) -> bool:
        """
        Generate and store embedding for a job.
        
        Args:
            job_id: Job ID (used as point ID)
            text: Job text to embed (title + description)
            metadata: Additional metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            logger.warning("Qdrant client not available")
            return False
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        if not embedding:
            return False
        
        # Prepare payload
        payload = {
            'job_id': job_id,
            'text': text,
            **(metadata or {})
        }
        
        try:
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            # Upsert point
            self._qdrant_client.upsert(
                collection_name=collection_name,
                points=[{
                    'id': job_id,
                    'vector': embedding,
                    'payload': payload,
                }]
            )
            
            logger.info(f"Stored embedding for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding for job {job_id}: {e}")
            return False
    
    def batch_store_embeddings(self, jobs_data: List[Dict]) -> Dict[str, int]:
        """
        Batch store embeddings for multiple jobs.
        
        Args:
            jobs_data: List of dicts with 'id', 'text', and optional 'metadata'
            
        Returns:
            Dict with 'success' and 'failed' counts
        """
        if not self.qdrant_client:
            return {'success': 0, 'failed': len(jobs_data)}
        
        points = []
        failed = 0
        
        for job_data in jobs_data:
            job_id = str(job_data.get('id', ''))
            text = job_data.get('text', '')
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            if not embedding:
                failed += 1
                continue
            
            # Prepare payload
            payload = {
                'job_id': job_id,
                'text': text,
                **(job_data.get('metadata', {}) or {})
            }
            
            points.append({
                'id': job_id,
                'vector': embedding,
                'payload': payload,
            })
        
        try:
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            # Batch upsert
            self._qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return {
                'success': len(points),
                'failed': failed,
            }
            
        except Exception as e:
            logger.error(f"Failed to batch store embeddings: {e}")
            return {'success': 0, 'failed': len(jobs_data)}
    
    def search_by_embedding(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search jobs by embedding similarity.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            List of matching jobs with scores
        """
        if not self.qdrant_client:
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []
        
        try:
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            # Search
            results = self._qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
            )
            
            # Format results
            formatted_results = []
            for point in results:
                formatted_results.append({
                    'job_id': point.payload.get('job_id'),
                    'score': point.score,
                    'text': point.payload.get('text', ''),
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search by embedding: {e}")
            return []
    
    def delete_job_embedding(self, job_id: str) -> bool:
        """
        Delete embedding for a job.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            return False
        
        try:
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            self._qdrant_client.delete(
                collection_name=collection_name,
                points_selector=[job_id]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding for job {job_id}: {e}")
            return False


# Singleton instance
embedding_service = EmbeddingService()


def generate_and_store_embedding(job_id: str, text: str, metadata: Dict = None) -> bool:
    """
    Convenience function to generate and store embedding.
    
    Args:
        job_id: Job ID
        text: Job text to embed
        metadata: Optional metadata
        
    Returns:
        True if successful, False otherwise
    """
    return embedding_service.store_embedding(job_id, text, metadata)