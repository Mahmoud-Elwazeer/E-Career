"""
AI Response Caching Service

Implements caching for AI responses to reduce costs and improve performance.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class AICacheService:
    """
    Service for caching AI responses.
    
    Caches:
    - Job recommendations
    - Career advice
    - Interview questions
    - Skill gap analysis
    - Profile completeness results
    """
    
    # Cache TTLs (in seconds)
    TTL = {
        'recommendations': 3600,  # 1 hour
        'career_advice': 7200,  # 2 hours
        'interview_questions': 1800,  # 30 minutes
        'skill_gap': 86400,  # 24 hours
        'completeness': 86400,  # 24 hours
        'default': 300,  # 5 minutes
    }
    
    def __init__(self):
        self.cache = cache
    
    def generate_cache_key(self, endpoint: str, user_id: str, params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            endpoint: API endpoint name
            user_id: User identifier
            params: Request parameters
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        
        # Create hash of params
        params_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:16]
        
        return f"ai_cache:{endpoint}:{user_id}:{params_hash}"
    
    def get(self, endpoint: str, user_id: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached response.
        
        Args:
            endpoint: API endpoint name
            user_id: User identifier
            params: Request parameters
            
        Returns:
            Cached response or None
        """
        cache_key = self.generate_cache_key(endpoint, user_id, params)
        
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(
                'Cache hit',
                endpoint=endpoint,
                user_id=user_id,
                cache_key=cache_key,
            )
            return cached
        
        logger.info(
            'Cache miss',
            endpoint=endpoint,
            user_id=user_id,
            cache_key=cache_key,
        )
        return None
    
    def set(
        self,
        endpoint: str,
        user_id: str,
        params: Dict[str, Any],
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a response.
        
        Args:
            endpoint: API endpoint name
            user_id: User identifier
            params: Request parameters
            response: Response data to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if caching succeeded
        """
        cache_key = self.generate_cache_key(endpoint, user_id, params)
        
        if ttl is None:
            ttl = self.TTL.get(endpoint, self.TTL['default'])
        
        # Add metadata
        cached_data = {
            'data': response,
            'cached_at': timezone.now().isoformat(),
            'endpoint': endpoint,
            'user_id': user_id,
        }
        
        self.cache.set(cache_key, cached_data, ttl)
        
        logger.info(
            'Cache set',
            endpoint=endpoint,
            user_id=user_id,
            ttl=ttl,
            cache_key=cache_key,
        )
        return True
    
    def delete(self, endpoint: str, user_id: str, params: Dict[str, Any]) -> bool:
        """
        Delete a cached response.
        
        Args:
            endpoint: API endpoint name
            user_id: User identifier
            params: Request parameters
            
        Returns:
            True if deletion succeeded
        """
        cache_key = self.generate_cache_key(endpoint, user_id, params)
        return self.cache.delete(cache_key)
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        Clear all cached responses for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of cache entries deleted
        """
        # Use cache pattern to find all user's cached items
        pattern = f"ai_cache:*:{user_id}:*"
        
        # Note: This requires cache backend support for pattern matching
        # For Redis, use SCAN; for other backends, iterate through keys
        deleted = 0
        
        # For Django cache, we need to iterate through keys
        # This is a simplified implementation
        from django.core.cache import caches
        cache = caches['default']
        
        # Get all keys and filter
        try:
            # Try to use cache's raw interface
            if hasattr(cache, 'keys'):
                keys = cache.keys(pattern)
                for key in keys:
                    cache.delete(key)
                    deleted += 1
        except Exception as e:
            logger.warning(f"Could not clear cache for user {user_id}: {e}")
        
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'type': 'ai_cache',
            'endpoints': list(self.TTL.keys()),
            'default_ttl': self.TTL['default'],
            'ttl_by_endpoint': self.TTL,
        }


def cache_ai_response(
    endpoint: str,
    user_id: str,
    params: Dict[str, Any],
    ttl: Optional[int] = None
):
    """
    Decorator to cache AI responses.
    
    Usage:
        @cache_ai_response('recommendations', 'user_id', {'job_id': '...'})
        def get_recommendations(user_id, job_id):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = AICacheService()
            
            # Try to get from cache
            cached = service.get(endpoint, user_id, params)
            if cached:
                return cached['data']
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            service.set(endpoint, user_id, params, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_on_update(model):
    """
    Decorator to invalidate cache when a model is updated.
    
    Usage:
        @invalidate_on_update(CareerProfile)
        def update_profile(user, data):
            ...
    """
    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver
    
    @receiver(post_save, sender=model)
    def invalidate_on_save(sender, instance, **kwargs):
        # Invalidate cache for this user
        user_id = str(instance.user.id) if hasattr(instance, 'user') else None
        if user_id:
            service = AICacheService()
            service.clear_user_cache(user_id)
    
    @receiver(post_delete, sender=model)
    def invalidate_on_delete(sender, instance, **kwargs):
        # Invalidate cache for this user
        user_id = str(instance.user.id) if hasattr(instance, 'user') else None
        if user_id:
            service = AICacheService()
            service.clear_user_cache(user_id)
    
    return model