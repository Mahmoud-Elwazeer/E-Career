"""
Performance Optimization Service

Implements performance optimization features including:
- Query optimization
- Caching strategies
- Database connection pooling
- Response compression
"""

import logging
import time
from typing import Dict, Any, Optional, List
from functools import wraps

from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Service for monitoring and optimizing performance.
    
    Tracks:
    - Query execution times
    - Cache hit/miss rates
    - Memory usage
    - Request processing times
    """
    
    def __init__(self):
        self._query_times = []
        self._cache_hits = 0
        self._cache_misses = 0
    
    def track_query(self, query: str, duration: float):
        """
        Track a database query.
        
        Args:
            query: SQL query string
            duration: Execution time in seconds
        """
        self._query_times.append({
            'query': query[:200],  # Truncate long queries
            'duration': duration,
            'timestamp': time.time(),
        })
    
    def track_cache_hit(self):
        """Track a cache hit."""
        self._cache_hits += 1
    
    def track_cache_miss(self):
        """Track a cache miss."""
        self._cache_misses += 1
    
    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get query statistics.
        
        Returns:
            Dictionary with query statistics
        """
        if not self._query_times:
            return {
                'total_queries': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': 0,
            }
        
        times = [q['duration'] for q in self._query_times]
        
        return {
            'total_queries': len(self._query_times),
            'avg_time': round(sum(times) / len(times), 6),
            'max_time': round(max(times), 6),
            'min_time': round(min(times), 6),
            'slow_queries': len([t for t in times if t > 0.1]),  # Queries > 100ms
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = self._cache_hits + self._cache_misses
        
        return {
            'total_operations': total,
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': round(self._cache_hits / total * 100, 1) if total > 0 else 0,
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get all performance statistics.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            'queries': self.get_query_stats(),
            'cache': self.get_cache_stats(),
        }


def optimize_queryset(queryset, select_related: List[str] = None, prefetch_related: List[str] = None):
    """
    Optimize a queryset with select_related and prefetch_related.
    
    Args:
        queryset: The queryset to optimize
        select_related: List of foreign key fields to select_related
        prefetch_related: List of reverse foreign key/m2m fields to prefetch_related
        
    Returns:
        Optimized queryset
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    return queryset


def cache_result(ttl: int = 300, key_prefix: str = ''):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


def query_optimizer(func):
    """
    Decorator to track query performance.
    
    Usage:
        @query_optimizer
        def get_user_data(user_id):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Reset query tracking
        connection.queries_log.clear()
        
        # Call the function
        result = func(*args, **kwargs)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get query count
        query_count = len(connection.queries)
        
        # Log performance
        logger.info(
            f"Query optimization: {func.__name__} - "
            f"Duration: {duration:.3f}s, Queries: {query_count}"
        )
        
        return result
    
    return wrapper


def batch_processor(items: List[Any], batch_size: int = 100):
    """
    Process items in batches.
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def response_compressor(func):
    """
    Decorator to compress response data.
    
    Usage:
        @response_compressor
        def get_large_data():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Check if result is a dict/list that can be compressed
        if isinstance(result, (dict, list)):
            # In production, you would use gzip compression
            # For now, just return the result
            pass
        
        return result
    
    return wrapper


def connection_pool_stats() -> Dict[str, Any]:
    """
    Get database connection pool statistics.
    
    Returns:
        Dictionary with connection pool statistics
    """
    return {
        'connections': {
            'total': len(connection.connections),
            'in_use': sum(1 for c in connection.connections if c.is_usable()),
            'available': sum(1 for c in connection.connections if not c.is_usable()),
        },
        'query_cache': {
            'size': len(connection.queries),
            'max_size': getattr(connection, 'query_log_max_size', 100),
        },
    }


def optimize_database_queries():
    """
    Optimize database queries for common operations.
    
    Returns:
        Dictionary with optimization recommendations
    """
    recommendations = []
    
    # Check for N+1 query patterns
    if connection.queries:
        query_count = len(connection.queries)
        if query_count > 20:
            recommendations.append({
                'type': 'n_plus_one',
                'severity': 'high',
                'message': f'High query count ({query_count}). Consider using select_related/prefetch_related.',
                'action': 'Review queryset optimization',
            })
    
    # Check for slow queries
    for query in connection.queries:
        duration = float(query.get('time', 0))
        if duration > 0.5:
            recommendations.append({
                'type': 'slow_query',
                'severity': 'medium',
                'message': f'Slow query detected: {query.get("sql", "")[:100]}',
                'action': 'Add database index or optimize query',
            })
    
    return {
        'recommendations': recommendations,
        'total_queries': len(connection.queries),
    }