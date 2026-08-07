"""
Rate Limiting Middleware

Implements per-endpoint rate limiting for API endpoints.
"""

import time
import logging
from collections import defaultdict
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for Django REST Framework.
    
    Implements sliding window rate limiting with configurable limits
    per endpoint and per user.
    """
    
    # Default rate limits (requests per window)
    DEFAULT_LIMITS = {
        'default': {'requests': 100, 'window': 60},  # 100 req/min
        'talent-score': {'requests': 10, 'window': 60},  # 10 req/min
        'career-brain': {'requests': 20, 'window': 60},  # 20 req/min
        'goals': {'requests': 30, 'window': 60},  # 30 req/min
        'rules': {'requests': 50, 'window': 60},  # 50 req/min
        'gdpr': {'requests': 5, 'window': 3600},  # 5 req/hour
        'auth': {'requests': 10, 'window': 300},  # 10 req/5min
        'scrape': {'requests': 5, 'window': 60},  # 5 req/min
    }
    
    def process_request(self, request):
        """Check rate limit before processing request."""
        # Skip rate limiting for non-API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Skip rate limiting for authenticated requests (admin)
        if request.user.is_staff or request.user.is_superuser:
            return None
        
        # Get rate limit configuration
        limit_config = self._get_limit_config(request.path)
        max_requests = limit_config['requests']
        window_seconds = limit_config['window']
        
        # Generate cache key
        cache_key = self._generate_cache_key(request, limit_config)
        
        # Get current request count
        current_time = time.time()
        requests = cache.get(cache_key, [])
        
        # Remove old requests outside the window
        requests = [t for t in requests if current_time - t < window_seconds]
        
        # Check if rate limit exceeded
        if len(requests) >= max_requests:
            logger.warning(
                'Rate limit exceeded',
                path=request.path,
                user=request.user.id if request.user.is_authenticated else 'anonymous',
                ip=request.META.get('REMOTE_ADDR'),
            )
            
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {max_requests} requests per {window_seconds} seconds',
                'retry_after': int(window_seconds - (current_time - requests[0])),
            }, status=429)
        
        # Add current request to the list
        requests.append(current_time)
        cache.set(cache_key, requests, window_seconds)
        
        return None
    
    def _get_limit_config(self, path):
        """Get rate limit configuration for a path."""
        # Check for specific endpoint limits
        endpoint_limits = {
            '/api/v1/career/talent-score/': 'talent-score',
            '/api/v1/career/scores/': 'talent-score',
            '/api/v1/career/career-brain/': 'career-brain',
            '/api/v1/career/goals/': 'goals',
            '/api/v1/career/goals/': 'goals',
            '/api/v1/career/completeness/': 'career-brain',
            '/api/v1/career/skill-gap/': 'career-brain',
            '/api/v1/core/rules/': 'rules',
            '/api/v1/core/feature-flags/': 'rules',
            '/api/v1/core/gdpr/': 'gdpr',
            '/api/v1/core/github/': 'auth',
            '/api/v1/jobs/scrape/': 'scrape',
        }
        
        for endpoint, limit_key in endpoint_limits.items():
            if path.startswith(endpoint):
                return self.DEFAULT_LIMITS[limit_key]
        
        return self.DEFAULT_LIMITS['default']
    
    def _generate_cache_key(self, request, limit_config):
        """Generate cache key for rate limiting."""
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Use user ID if authenticated, otherwise use IP
        identifier = user_id if request.user.is_authenticated else ip_address
        
        return f"ratelimit:{request.path}:{identifier}:{limit_config['requests']}:{limit_config['window']}"


class BurstRateLimitMiddleware(MiddlewareMixin):
    """
    Burst rate limiting middleware.
    
    Prevents burst attacks by limiting rapid consecutive requests.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.burst_limits = defaultdict(list)
        self.burst_window = 1  # 1 second window
        self.max_burst = 5  # Max 5 requests per second
    
    def process_request(self, request):
        """Check for burst requests."""
        if not request.path.startswith('/api/'):
            return None
        
        # Skip for authenticated users
        if request.user.is_authenticated:
            return None
        
        current_time = time.time()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Clean old burst records
        self.burst_limits[ip_address] = [
            t for t in self.burst_limits[ip_address]
            if current_time - t < self.burst_window
        ]
        
        # Check burst limit
        if len(self.burst_limits[ip_address]) >= self.max_burst:
            return JsonResponse({
                'error': 'Too many requests',
                'message': 'Too many requests in a short time',
            }, status=429)
        
        # Record this request
        self.burst_limits[ip_address].append(current_time)
        
        return None


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass