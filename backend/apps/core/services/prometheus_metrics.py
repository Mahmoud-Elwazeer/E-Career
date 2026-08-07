"""
Prometheus Metrics Service

Implements Prometheus-compatible metrics for monitoring and alerting.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps

from django.core.cache import cache

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """
    Service for collecting Prometheus-compatible metrics.
    
    Metrics:
    - HTTP request counts
    - Request duration histograms
    - Error rates
    - Cache hit/miss rates
    - Database query counts
    - Custom business metrics
    """
    
    def __init__(self):
        self._metrics = {
            'http_requests_total': {},
            'http_request_duration_seconds': {},
            'http_requests_errors_total': {},
            'cache_hits_total': 0,
            'cache_misses_total': 0,
            'database_queries_total': 0,
            'database_query_duration_seconds': 0,
            'ai_requests_total': {},
            'ai_request_duration_seconds': {},
            'ai_tokens_total': {},
        }
        self._start_time = time.time()
    
    def increment_http_requests(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float
    ):
        """
        Increment HTTP request counter.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration: Request duration in seconds
        """
        key = f"{method}:{path}"
        
        if key not in self._metrics['http_requests_total']:
            self._metrics['http_requests_total'][key] = {
                'total': 0,
                'status_codes': {},
            }
        
        self._metrics['http_requests_total'][key]['total'] += 1
        
        status_key = str(status_code)
        if status_key not in self._metrics['http_requests_total'][key]['status_codes']:
            self._metrics['http_requests_total'][key]['status_codes'][status_key] = 0
        self._metrics['http_requests_total'][key]['status_codes'][status_key] += 1
        
        # Track duration
        if key not in self._metrics['http_request_duration_seconds']:
            self._metrics['http_request_duration_seconds'][key] = {
                'sum': 0,
                'count': 0,
                'histogram': {},
            }
        
        self._metrics['http_request_duration_seconds'][key]['sum'] += duration
        self._metrics['http_request_duration_seconds'][key]['count'] += 1
        
        # Add to histogram buckets
        for bucket in [0.1, 0.5, 1.0, 5.0, 10.0]:
            if duration <= bucket:
                bucket_key = f"le_{bucket}"
                if bucket_key not in self._metrics['http_request_duration_seconds'][key]['histogram']:
                    self._metrics['http_request_duration_seconds'][key]['histogram'][bucket_key] = 0
                self._metrics['http_request_duration_seconds'][key]['histogram'][bucket_key] += 1
                break
        
        # Track errors
        if status_code >= 400:
            error_key = f"{method}:{path}"
            if error_key not in self._metrics['http_requests_errors_total']:
                self._metrics['http_requests_errors_total'][error_key] = 0
            self._metrics['http_requests_errors_total'][error_key] += 1
    
    def increment_cache_hits(self, count: int = 1):
        """Increment cache hits counter."""
        self._metrics['cache_hits_total'] += count
    
    def increment_cache_misses(self, count: int = 1):
        """Increment cache misses counter."""
        self._metrics['cache_misses_total'] += count
    
    def increment_database_queries(self, count: int = 1, duration: float = 0):
        """Increment database query counter."""
        self._metrics['database_queries_total'] += count
        self._metrics['database_query_duration_seconds'] += duration
    
    def increment_ai_requests(
        self,
        model: str,
        duration: float,
        input_tokens: int,
        output_tokens: int
    ):
        """Increment AI request counter."""
        if model not in self._metrics['ai_requests_total']:
            self._metrics['ai_requests_total'][model] = 0
        
        self._metrics['ai_requests_total'][model] += 1
        
        # Track duration
        if model not in self._metrics['ai_request_duration_seconds']:
            self._metrics['ai_request_duration_seconds'][model] = {
                'sum': 0,
                'count': 0,
            }
        
        self._metrics['ai_request_duration_seconds'][model]['sum'] += duration
        self._metrics['ai_request_duration_seconds'][model]['count'] += 1
        
        # Track tokens
        if model not in self._metrics['ai_tokens_total']:
            self._metrics['ai_tokens_total'][model] = {
                'input': 0,
                'output': 0,
            }
        
        self._metrics['ai_tokens_total'][model]['input'] += input_tokens
        self._metrics['ai_tokens_total'][model]['output'] += output_tokens
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.
        
        Returns:
            Dictionary with all metrics
        """
        uptime = time.time() - self._start_time
        
        # Calculate averages
        http_metrics = {}
        for key, data in self._metrics['http_requests_total'].items():
            http_metrics[key] = {
                'total': data['total'],
                'status_codes': data['status_codes'],
                'avg_duration': round(
                    self._metrics['http_request_duration_seconds'].get(key, {}).get('sum', 0) / 
                    max(self._metrics['http_request_duration_seconds'].get(key, {}).get('count', 1), 1),
                    6
                ),
            }
        
        ai_metrics = {}
        for model, count in self._metrics['ai_requests_total'].items():
            ai_metrics[model] = {
                'total': count,
                'avg_duration': round(
                    self._metrics['ai_request_duration_seconds'].get(model, {}).get('sum', 0) / 
                    max(count, 1),
                    6
                ),
                'input_tokens': self._metrics['ai_tokens_total'].get(model, {}).get('input', 0),
                'output_tokens': self._metrics['ai_tokens_total'].get(model, {}).get('output', 0),
            }
        
        return {
            'uptime_seconds': round(uptime, 2),
            'timestamp': datetime.now().isoformat(),
            'http_requests': http_metrics,
            'http_errors': self._metrics['http_requests_errors_total'],
            'cache': {
                'hits': self._metrics['cache_hits_total'],
                'misses': self._metrics['cache_misses_total'],
                'hit_rate': round(
                    self._metrics['cache_hits_total'] / 
                    max(self._metrics['cache_hits_total'] + self._metrics['cache_misses_total'], 1) * 100,
                    1
                ),
            },
            'database': {
                'queries': self._metrics['database_queries_total'],
                'total_duration_seconds': round(self._metrics['database_query_duration_seconds'], 6),
            },
            'ai': ai_metrics,
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._metrics = {
            'http_requests_total': {},
            'http_request_duration_seconds': {},
            'http_requests_errors_total': {},
            'cache_hits_total': 0,
            'cache_misses_total': 0,
            'database_queries_total': 0,
            'database_query_duration_seconds': 0,
            'ai_requests_total': {},
            'ai_request_duration_seconds': {},
            'ai_tokens_total': {},
        }
        self._start_time = time.time()


def track_http_request(func):
    """
    Decorator to track HTTP request metrics.
    
    Usage:
        @track_http_request
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        try:
            response = func(request, *args, **kwargs)
            duration = time.time() - start_time
            
            # Track metrics
            metrics = PrometheusMetrics()
            metrics.increment_http_requests(
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration=duration,
            )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            
            # Track error metrics
            metrics = PrometheusMetrics()
            metrics.increment_http_requests(
                method=request.method,
                path=request.path,
                status_code=500,
                duration=duration,
            )
            
            raise
    
    return wrapper


def track_ai_request(func):
    """
    Decorator to track AI request metrics.
    
    Usage:
        @track_ai_request
        def generate_recommendations(user_id):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Track metrics (you would extract model and tokens from result)
            metrics = PrometheusMetrics()
            metrics.increment_ai_requests(
                model='claude-3-5-sonnet',
                duration=duration,
                input_tokens=0,  # Extract from actual request
                output_tokens=0,  # Extract from actual response
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Track error metrics
            metrics = PrometheusMetrics()
            metrics.increment_ai_requests(
                model='claude-3-5-sonnet',
                duration=duration,
                input_tokens=0,
                output_tokens=0,
            )
            
            raise
    
    return wrapper