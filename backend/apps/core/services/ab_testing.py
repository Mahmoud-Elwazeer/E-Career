"""
A/B Testing Framework

Implements A/B testing for feature flags and UI variations.
"""

import logging
import random
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

from django.core.cache import cache

logger = logging.getLogger(__name__)


class ABTestingService:
    """
    Service for A/B testing.
    
    Features:
    - Feature flag testing
    - UI variation testing
    - Conversion tracking
    - Statistical significance
    """
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize A/B testing service.
        
        Args:
            user_id: Optional user identifier for consistent assignment
        """
        self.user_id = user_id
        self._experiments = {}
        self._assignments = {}
    
    def _generate_experiment_key(self, experiment_name: str, user_id: str) -> str:
        """Generate a consistent key for user assignment."""
        key = f"{experiment_name}:{user_id}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def assign_variation(
        self,
        experiment_name: str,
        variations: List[str],
        weights: Optional[List[float]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Assign a user to a variation.
        
        Args:
            experiment_name: Name of the experiment
            variations: List of variation names
            weights: Optional weights for each variation (must sum to 1.0)
            user_id: Optional user identifier
            
        Returns:
            Assigned variation name
        """
        if user_id is None:
            user_id = self.user_id
        
        if user_id is None:
            # Random assignment for anonymous users
            if weights is None:
                weights = [1.0 / len(variations)] * len(variations)
            return random.choices(variations, weights=weights)[0]
        
        # Generate consistent key for user
        key = self._generate_experiment_key(experiment_name, user_id)
        
        # Check cache for existing assignment
        cached = cache.get(f"ab_assignment:{key}")
        if cached:
            return cached
        
        # Calculate weights
        if weights is None:
            weights = [1.0 / len(variations)] * len(variations)
        
        # Assign variation based on hash
        hash_value = int(key[:8], 16) / 0xFFFFFFFF
        cumulative = 0
        for variation, weight in zip(variations, weights):
            cumulative += weight
            if hash_value < cumulative:
                # Cache the assignment
                cache.set(f"ab_assignment:{key}", variation, 86400)  # 24 hours
                return variation
        
        # Fallback to last variation
        return variations[-1]
    
    def is_experiment_active(self, experiment_name: str) -> bool:
        """
        Check if an experiment is active.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            True if experiment is active
        """
        return experiment_name in self._experiments
    
    def track_conversion(
        self,
        experiment_name: str,
        variation: str,
        conversion_type: str = 'default',
        user_id: Optional[str] = None
    ) -> bool:
        """
        Track a conversion for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            variation: Assigned variation
            conversion_type: Type of conversion
            user_id: Optional user identifier
            
        Returns:
            True if tracking succeeded
        """
        if user_id is None:
            user_id = self.user_id
        
        if user_id is None:
            logger.warning("Cannot track conversion without user_id")
            return False
        
        # Update conversion count
        cache_key = f"ab_conversion:{experiment_name}:{variation}:{conversion_type}"
        current = cache.get(cache_key, 0)
        cache.set(cache_key, current + 1, 86400)  # 24 hours
        
        # Update total exposure count
        exposure_key = f"ab_exposure:{experiment_name}:{variation}"
        exposure = cache.get(exposure_key, 0)
        cache.set(exposure_key, exposure + 1, 86400)
        
        logger.info(
            'Conversion tracked',
            experiment=experiment_name,
            variation=variation,
            conversion_type=conversion_type,
            user_id=user_id,
        )
        
        return True
    
    def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """
        Get results for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            Dictionary with experiment results
        """
        # Get exposure counts
        variations = self._experiments.get(experiment_name, {}).get('variations', [])
        
        results = {
            'experiment_name': experiment_name,
            'variations': {},
            'total_exposures': 0,
            'total_conversions': 0,
        }
        
        for variation in variations:
            exposure_key = f"ab_exposure:{experiment_name}:{variation}"
            exposure = cache.get(exposure_key, 0)
            
            results['variations'][variation] = {
                'exposures': exposure,
                'conversions': {},
            }
            
            results['total_exposures'] += exposure
            
            # Get conversion counts
            for conversion_type in ['default', 'signup', 'purchase']:
                conversion_key = f"ab_conversion:{experiment_name}:{variation}:{conversion_type}"
                conversion = cache.get(conversion_key, 0)
                results['variations'][variation]['conversions'][conversion_type] = conversion
                results['total_conversions'] += conversion
        
        # Calculate conversion rates
        for variation in variations:
            exposures = results['variations'][variation]['exposures']
            if exposures > 0:
                results['variations'][variation]['conversion_rate'] = round(
                    results['variations'][variation]['conversions']['default'] / exposures * 100, 2
                )
            else:
                results['variations'][variation]['conversion_rate'] = 0
        
        return results
    
    def create_experiment(
        self,
        experiment_name: str,
        variations: List[str],
        weights: Optional[List[float]] = None,
        description: str = ''
    ) -> Dict[str, Any]:
        """
        Create a new experiment.
        
        Args:
            experiment_name: Name of the experiment
            variations: List of variation names
            weights: Optional weights for each variation
            description: Optional description
            
        Returns:
            Created experiment configuration
        """
        self._experiments[experiment_name] = {
            'variations': variations,
            'weights': weights or [1.0 / len(variations)] * len(variations),
            'description': description,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
        }
        
        return self._experiments[experiment_name]
    
    def get_user_assignment(self, experiment_name: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Get a user's assignment for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            user_id: Optional user identifier
            
        Returns:
            Assigned variation or None
        """
        if user_id is None:
            user_id = self.user_id
        
        if user_id is None:
            return None
        
        key = self._generate_experiment_key(experiment_name, user_id)
        return cache.get(f"ab_assignment:{key}")
    
    def get_all_experiments(self) -> Dict[str, Any]:
        """
        Get all experiments.
        
        Returns:
            Dictionary with all experiments
        """
        return self._experiments
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get A/B testing statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'type': 'ab_testing',
            'experiments_count': len(self._experiments),
            'experiments': list(self._experiments.keys()),
        }


def check_feature_flag(feature_name: str, user_id: Optional[str] = None) -> bool:
    """
    Check if a feature flag is enabled for a user.
    
    Args:
        feature_name: Name of the feature flag
        user_id: Optional user identifier
        
    Returns:
        True if feature is enabled
    """
    # Default: 50% of users get the feature
    ab_service = ABTestingService(user_id)
    
    # Create experiment if not exists
    if feature_name not in ab_service._experiments:
        ab_service.create_experiment(
            experiment_name=feature_name,
            variations=['enabled', 'disabled'],
            weights=[0.5, 0.5],
            description=f'Feature flag: {feature_name}',
        )
    
    # Assign variation
    variation = ab_service.assign_variation(
        experiment_name=feature_name,
        variations=['enabled', 'disabled'],
        weights=[0.5, 0.5],
    )
    
    return variation == 'enabled'


def get_feature_flags(user_id: Optional[str] = None) -> Dict[str, bool]:
    """
    Get all feature flags for a user.
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        Dictionary with feature flags
    """
    # Define feature flags
    features = [
        'new_dashboard',
        'dark_mode',
        'ai_recommendations',
        'skill_gap_analysis',
        'career_goals',
        'performance_dashboard',
        'cost_tracking',
    ]
    
    return {
        feature: check_feature_flag(feature, user_id)
        for feature in features
    }