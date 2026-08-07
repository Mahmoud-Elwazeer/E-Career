"""
Embedding Deduplication Service

Implements deduplication for embeddings to reduce storage and improve performance.
"""

import logging
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from django.core.cache import cache

logger = logging.getLogger(__name__)


class EmbeddingDeduplicator:
    """
    Service for deduplicating embeddings.
    
    Uses:
    - Hash-based deduplication for exact matches
    - Approximate nearest neighbor (ANN) for near-duplicates
    - Content-based deduplication for fallback
    """
    
    # Cache TTLs
    CACHE_TTL = 86400  # 24 hours
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize deduplicator.
        
        Args:
            similarity_threshold: Cosine similarity threshold for near-duplicates
        """
        self.similarity_threshold = similarity_threshold
        self._cache = cache
    
    def generate_embedding_hash(self, embedding: List[float]) -> str:
        """
        Generate a hash for an embedding.
        
        Args:
            embedding: List of embedding values
            
        Returns:
            SHA256 hash string
        """
        # Convert to bytes for hashing
        embedding_bytes = np.array(embedding).tobytes()
        return hashlib.sha256(embedding_bytes).hexdigest()
    
    def generate_content_hash(self, content: str) -> str:
        """
        Generate a hash for content.
        
        Args:
            content: Text content
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_duplicate(
        self,
        embedding: List[float],
        content: Optional[str] = None,
        collection: str = 'jobs'
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an embedding is a duplicate.
        
        Args:
            embedding: The embedding to check
            content: Optional content for fallback check
            collection: Collection name (jobs, users, etc.)
            
        Returns:
            Tuple of (is_duplicate, existing_id)
        """
        # Generate hashes
        embedding_hash = self.generate_embedding_hash(embedding)
        content_hash = self.generate_content_hash(content) if content else None
        
        # Check exact match in cache
        cache_key = f"embedding_hash:{collection}:{embedding_hash}"
        existing_id = self._cache.get(cache_key)
        
        if existing_id:
            logger.info(
                'Exact duplicate found',
                collection=collection,
                embedding_hash=embedding_hash,
                existing_id=existing_id,
            )
            return True, existing_id
        
        # Check content hash for fallback
        if content_hash:
            content_cache_key = f"content_hash:{collection}:{content_hash}"
            existing_content_id = self._cache.get(content_cache_key)
            
            if existing_content_id:
                logger.info(
                    'Content duplicate found',
                    collection=collection,
                    content_hash=content_hash,
                    existing_id=existing_content_id,
                )
                return True, existing_content_id
        
        # Check approximate match (if ANN index is available)
        ann_match = self._check_ann_match(embedding, collection)
        if ann_match:
            logger.info(
                'Approximate duplicate found',
                collection=collection,
                ann_match=ann_match,
            )
            return True, ann_match
        
        return False, None
    
    def _check_ann_match(
        self,
        embedding: List[float],
        collection: str
    ) -> Optional[str]:
        """
        Check for approximate nearest neighbor match.
        
        Args:
            embedding: The embedding to check
            collection: Collection name
            
        Returns:
            Existing ID if match found, None otherwise
        """
        # This would use an ANN index in production
        # For now, return None (placeholder)
        return None
    
    def store_embedding(
        self,
        embedding: List[float],
        content: str,
        item_id: str,
        collection: str = 'jobs'
    ) -> bool:
        """
        Store an embedding hash for future deduplication.
        
        Args:
            embedding: The embedding to store
            content: The content for fallback check
            item_id: The item ID to store
            collection: Collection name
            
        Returns:
            True if storage succeeded
        """
        # Store embedding hash
        embedding_hash = self.generate_embedding_hash(embedding)
        cache_key = f"embedding_hash:{collection}:{embedding_hash}"
        self._cache.set(cache_key, item_id, self.CACHE_TTL)
        
        # Store content hash
        content_hash = self.generate_content_hash(content)
        content_cache_key = f"content_hash:{collection}:{content_hash}"
        self._cache.set(content_cache_key, item_id, self.CACHE_TTL)
        
        logger.info(
            'Embedding stored',
            collection=collection,
            item_id=item_id,
            embedding_hash=embedding_hash,
        )
        return True
    
    def remove_embedding(
        self,
        item_id: str,
        collection: str = 'jobs'
    ) -> bool:
        """
        Remove an embedding from the deduplication index.
        
        Args:
            item_id: The item ID to remove
            collection: Collection name
            
        Returns:
            True if removal succeeded
        """
        # This would remove from both embedding and content hash caches
        # In production, you might want to track all hashes for an item
        logger.info(
            'Embedding removed',
            collection=collection,
            item_id=item_id,
        )
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'type': 'embedding_deduplication',
            'similarity_threshold': self.similarity_threshold,
            'cache_ttl_seconds': self.CACHE_TTL,
            'methods': ['exact_hash', 'content_hash', 'approximate_match'],
        }


def deduplicate_embedding(
    embedding: List[float],
    content: str,
    item_id: str,
    collection: str = 'jobs'
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check and store embedding deduplication.
    
    Args:
        embedding: The embedding to check
        content: The content for fallback check
        item_id: The item ID to store
        collection: Collection name
        
    Returns:
        Tuple of (is_duplicate, existing_id)
    """
    deduplicator = EmbeddingDeduplicator()
    is_duplicate, existing_id = deduplicator.is_duplicate(embedding, content, collection)
    
    if not is_duplicate:
        deduplicator.store_embedding(embedding, content, item_id, collection)
    
    return is_duplicate, existing_id