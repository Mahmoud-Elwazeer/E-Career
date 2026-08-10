"""
Redis Caching Service - Phase E Performance Optimization

Centralized caching layer for high-traffic endpoints.
Uses Django's cache framework with Redis backend.
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

# Cache timeout constants (in seconds)
CACHE_TIMEOUT_SHORT = 60 * 5  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 60 * 15  # 15 minutes
CACHE_TIMEOUT_LONG = 60 * 60  # 1 hour
CACHE_TIMEOUT_VERY_LONG = 60 * 60 * 24  # 24 hours


def make_cache_key(*args, prefix: str = "", **kwargs) -> str:
    """
    Generate a cache key from arguments.

    Args:
        *args: Positional arguments to include in key
        prefix: Key prefix (e.g., 'jobs', 'user', 'company')
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    key_parts = [prefix] if prefix else []

    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        else:
            # Hash complex objects
            key_parts.append(hashlib.md5(
                json.dumps(arg, sort_keys=True, default=str).encode()
            ).hexdigest()[:8])

    # Add keyword args
    if kwargs:
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

    return ":".join(key_parts)


def cached(timeout: int = CACHE_TIMEOUT_MEDIUM, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Usage:
        @cached(timeout=300, key_prefix="jobs")
        def get_featured_jobs():
            return Job.objects.filter(is_featured=True)[:10]

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = make_cache_key(
                func.__name__,
                *args,
                prefix=key_prefix,
                **kwargs
            )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return result

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, timeout)

            return result

        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    Invalidate cached data by key prefix.

    Usage:
        invalidate_cache("jobs", job_id=123)
        invalidate_cache("user", user_id=456)
    """
    cache_key = make_cache_key(*args, prefix=key_prefix, **kwargs)
    cache.delete(cache_key)
    logger.info(f"Cache invalidated: {cache_key}")


def invalidate_pattern(pattern: str):
    """
    Invalidate all keys matching a pattern.

    Usage:
        invalidate_pattern("jobs:*")
        invalidate_pattern("user:123:*")

    Note: Requires Redis backend with delete_pattern support
    """
    try:
        if hasattr(cache, 'delete_pattern'):
            count = cache.delete_pattern(pattern)
            logger.info(f"Cache pattern invalidated: {pattern} ({count} keys)")
        else:
            logger.warning("Cache backend doesn't support pattern deletion")
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")


# ============================================================================
# Pre-defined cache functions for common queries
# ============================================================================


def cache_job_list(filters: dict, timeout: int = CACHE_TIMEOUT_MEDIUM) -> Optional[Any]:
    """
    Cache job listing results.

    Args:
        filters: Query filters (location, skills, etc.)
        timeout: Cache duration
    """
    cache_key = make_cache_key("job_list", **filters)
    return cache.get(cache_key)


def set_cache_job_list(filters: dict, data: Any, timeout: int = CACHE_TIMEOUT_MEDIUM):
    """Store job listing in cache"""
    cache_key = make_cache_key("job_list", **filters)
    cache.set(cache_key, data, timeout)
    logger.debug(f"Cached job list: {cache_key}")


def cache_job_detail(job_id: str, timeout: int = CACHE_TIMEOUT_LONG) -> Optional[Any]:
    """Cache single job detail"""
    cache_key = f"job:detail:{job_id}"
    return cache.get(cache_key)


def set_cache_job_detail(job_id: str, data: Any, timeout: int = CACHE_TIMEOUT_LONG):
    """Store job detail in cache"""
    cache_key = f"job:detail:{job_id}"
    cache.set(cache_key, data, timeout)


def invalidate_job_cache(job_id: str):
    """Invalidate all caches related to a job"""
    cache.delete(f"job:detail:{job_id}")
    invalidate_pattern(f"job_list:*")  # Invalidate all listing caches
    logger.info(f"Invalidated job cache: {job_id}")


def cache_user_profile(user_id: str, timeout: int = CACHE_TIMEOUT_MEDIUM) -> Optional[Any]:
    """Cache user profile data"""
    cache_key = f"user:profile:{user_id}"
    return cache.get(cache_key)


def set_cache_user_profile(user_id: str, data: Any, timeout: int = CACHE_TIMEOUT_MEDIUM):
    """Store user profile in cache"""
    cache_key = f"user:profile:{user_id}"
    cache.set(cache_key, data, timeout)


def invalidate_user_cache(user_id: str):
    """Invalidate all caches related to a user"""
    invalidate_pattern(f"user:{user_id}:*")
    logger.info(f"Invalidated user cache: {user_id}")


def cache_company_data(company_id: str, timeout: int = CACHE_TIMEOUT_VERY_LONG) -> Optional[Any]:
    """Cache company data (rarely changes)"""
    cache_key = f"company:{company_id}"
    return cache.get(cache_key)


def set_cache_company_data(company_id: str, data: Any, timeout: int = CACHE_TIMEOUT_VERY_LONG):
    """Store company data in cache"""
    cache_key = f"company:{company_id}"
    cache.set(cache_key, data, timeout)


def cache_stats(stat_type: str, timeout: int = CACHE_TIMEOUT_LONG) -> Optional[Any]:
    """
    Cache dashboard statistics.

    Args:
        stat_type: Type of stats (e.g., 'daily', 'weekly', 'monthly')
    """
    cache_key = f"stats:{stat_type}"
    return cache.get(cache_key)


def set_cache_stats(stat_type: str, data: Any, timeout: int = CACHE_TIMEOUT_LONG):
    """Store statistics in cache"""
    cache_key = f"stats:{stat_type}"
    cache.set(cache_key, data, timeout)


# ============================================================================
# Cache warming utilities
# ============================================================================


def warm_cache():
    """
    Pre-populate cache with frequently accessed data.

    Run this after deployments or cache flushes.
    """
    from apps.jobs.models import Job
    from apps.jobs.serializers import JobListSerializer

    logger.info("Starting cache warming...")

    # Warm featured jobs
    featured_jobs = Job.objects.filter(is_featured=True, status='active')[:20]
    serializer = JobListSerializer(featured_jobs, many=True)
    set_cache_job_list({'featured': True}, serializer.data)

    # Warm recent jobs
    recent_jobs = Job.objects.filter(status='active').order_by('-posted_at')[:50]
    serializer = JobListSerializer(recent_jobs, many=True)
    set_cache_job_list({'recent': True}, serializer.data)

    logger.info("Cache warming complete")


def get_cache_stats() -> dict:
    """
    Get cache performance statistics.

    Returns:
        Dict with cache hits, misses, etc.
    """
    try:
        if hasattr(cache, 'get_stats'):
            return cache.get_stats()
        return {'message': 'Cache stats not available for this backend'}
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {'error': str(e)}
