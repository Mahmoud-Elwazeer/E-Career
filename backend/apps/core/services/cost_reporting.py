"""
Cost Reporting Service

Implements per-user AI budget tracking and cost reporting.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class CostReportingService:
    """
    Service for tracking and reporting AI costs.
    
    Tracks:
    - Per-user AI budget
    - Cost by endpoint
    - Cost by model
    - Cost by day/week/month
    """
    
    # Default budgets (in USD)
    DEFAULT_DAILY_BUDGET = 10.0
    DEFAULT_MONTHLY_BUDGET = 100.0
    
    # Cost estimates (per 1M tokens)
    COST_PER_MILLION_TOKENS = {
        'claude-3-5-sonnet': {'input': 3.00, 'output': 15.00},
        'claude-3-opus': {'input': 15.00, 'output': 75.00},
        'claude-3-haiku': {'input': 0.25, 'output': 1.25},
        'embed-english': {'input': 0.10, 'output': 0.0},
        'embed-multilingual': {'input': 0.10, 'output': 0.0},
    }
    
    def __init__(self, user_id: str):
        """
        Initialize cost reporting service.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.cache = cache
    
    def _get_cache_key(self, date_str: str, endpoint: str) -> str:
        """Generate cache key for cost tracking."""
        return f"cost:{self.user_id}:{date_str}:{endpoint}"
    
    def record_cost(
        self,
        endpoint: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Record an AI cost.
        
        Args:
            endpoint: API endpoint
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Optional explicit cost (calculated if not provided)
            
        Returns:
            Cost record
        """
        today = timezone.now().date().isoformat()
        
        # Calculate cost if not provided
        if cost is None:
            cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Update daily cost
        daily_key = self._get_cache_key(today, endpoint)
        daily_data = self.cache.get(daily_key, {
            'total_cost': 0.0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'requests': 0,
        })
        
        daily_data['total_cost'] += cost
        daily_data['total_input_tokens'] += input_tokens
        daily_data['total_output_tokens'] += output_tokens
        daily_data['requests'] += 1
        
        self.cache.set(daily_key, daily_data, 86400)  # 24 hours
        
        # Update monthly cost
        monthly_key = f"cost:{self.user_id}:{today[:7]}"  # YYYY-MM
        monthly_data = self.cache.get(monthly_key, {
            'total_cost': 0.0,
            'endpoints': {},
        })
        
        monthly_data['total_cost'] += cost
        if endpoint not in monthly_data['endpoints']:
            monthly_data['endpoints'][endpoint] = {
                'total_cost': 0.0,
                'requests': 0,
            }
        monthly_data['endpoints'][endpoint]['total_cost'] += cost
        monthly_data['endpoints'][endpoint]['requests'] += 1
        
        self.cache.set(monthly_key, monthly_data, 2592000)  # 30 days
        
        logger.info(
            'Cost recorded',
            user_id=self.user_id,
            endpoint=endpoint,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        
        return {
            'user_id': self.user_id,
            'date': today,
            'endpoint': endpoint,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
        }
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token counts."""
        if model not in self.COST_PER_MILLION_TOKENS:
            # Default cost estimate
            return (input_tokens + output_tokens) * 0.000001 * 5.0
        
        costs = self.COST_PER_MILLION_TOKENS[model]
        input_cost = (input_tokens / 1_000_000) * costs['input']
        output_cost = (output_tokens / 1_000_000) * costs['output']
        
        return round(input_cost + output_cost, 6)
    
    def get_daily_cost(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily cost summary.
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Daily cost summary
        """
        if date is None:
            date = timezone.now().date().isoformat()
        
        # Get all endpoint costs for the day
        daily_costs = {}
        total_cost = 0.0
        
        for endpoint in ['talent-score', 'career-brain', 'goals', 'rules', 'default']:
            key = self._get_cache_key(date, endpoint)
            data = self.cache.get(key, {})
            
            if data:
                daily_costs[endpoint] = {
                    'total_cost': data.get('total_cost', 0),
                    'requests': data.get('requests', 0),
                    'input_tokens': data.get('total_input_tokens', 0),
                    'output_tokens': data.get('total_output_tokens', 0),
                }
                total_cost += data.get('total_cost', 0)
        
        return {
            'user_id': self.user_id,
            'date': date,
            'total_cost': round(total_cost, 6),
            'endpoints': daily_costs,
            'budget_used': round(total_cost / self.DEFAULT_DAILY_BUDGET * 100, 1),
        }
    
    def get_monthly_cost(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get monthly cost summary.
        
        Args:
            date: Date string (YYYY-MM), defaults to current month
            
        Returns:
            Monthly cost summary
        """
        if date is None:
            date = timezone.now().strftime('%Y-%m')
        
        monthly_key = f"cost:{self.user_id}:{date}"
        data = self.cache.get(monthly_key, {
            'total_cost': 0.0,
            'endpoints': {},
        })
        
        return {
            'user_id': self.user_id,
            'month': date,
            'total_cost': round(data.get('total_cost', 0), 6),
            'endpoints': data.get('endpoints', {}),
            'budget_used': round(data.get('total_cost', 0) / self.DEFAULT_MONTHLY_BUDGET * 100, 1),
        }
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.
        
        Returns:
            Budget status information
        """
        today = timezone.now().date().isoformat()
        current_month = timezone.now().strftime('%Y-%m')
        
        daily_cost = self.get_daily_cost(today)
        monthly_cost = self.get_monthly_cost(current_month)
        
        return {
            'user_id': self.user_id,
            'daily_budget': self.DEFAULT_DAILY_BUDGET,
            'daily_spent': daily_cost['total_cost'],
            'daily_remaining': round(self.DEFAULT_DAILY_BUDGET - daily_cost['total_cost'], 2),
            'daily_usage_percent': daily_cost['budget_used'],
            'monthly_budget': self.DEFAULT_MONTHLY_BUDGET,
            'monthly_spent': monthly_cost['total_cost'],
            'monthly_remaining': round(self.DEFAULT_MONTHLY_BUDGET - monthly_cost['total_cost'], 2),
            'monthly_usage_percent': monthly_cost['budget_used'],
            'is_daily_limit_exceeded': daily_cost['total_cost'] >= self.DEFAULT_DAILY_BUDGET,
            'is_monthly_limit_exceeded': monthly_cost['total_cost'] >= self.DEFAULT_MONTHLY_BUDGET,
        }
    
    def get_cost_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get cost history for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of daily cost summaries
        """
        history = []
        
        for i in range(days):
            date = (timezone.now().date() - timedelta(days=i)).isoformat()
            cost = self.get_daily_cost(date)
            
            if cost['total_cost'] > 0:
                history.append({
                    'date': date,
                    'total_cost': cost['total_cost'],
                    'endpoints': cost['endpoints'],
                })
        
        # Sort by date (oldest first)
        history.sort(key=lambda x: x['date'])
        
        return history
    
    def reset_budget(self) -> bool:
        """
        Reset daily budget (for testing).
        
        Returns:
            True if reset succeeded
        """
        today = timezone.now().date().isoformat()
        
        for endpoint in ['talent-score', 'career-brain', 'goals', 'rules', 'default']:
            key = self._get_cache_key(today, endpoint)
            self.cache.delete(key)
        
        monthly_key = f"cost:{self.user_id}:{today[:7]}"
        self.cache.delete(monthly_key)
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cost reporting statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'type': 'cost_reporting',
            'user_id': self.user_id,
            'default_daily_budget': self.DEFAULT_DAILY_BUDGET,
            'default_monthly_budget': self.DEFAULT_MONTHLY_BUDGET,
            'cost_per_million_tokens': self.COST_PER_MILLION_TOKENS,
        }


def get_user_cost_summary(user_id: str) -> Dict[str, Any]:
    """
    Get cost summary for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Cost summary
    """
    service = CostReportingService(user_id)
    return service.get_budget_status()