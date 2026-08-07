"""
Prompt Versioning Service

Implements versioning for AI prompts to enable rollback and A/B testing.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from django.core.cache import cache

logger = logging.getLogger(__name__)


class PromptVersion(Enum):
    """Prompt version identifiers."""
    V1 = 'v1'
    V2 = 'v2'
    V3 = 'v3'
    LATEST = 'latest'


class PromptTemplate:
    """
    Template for AI prompts with versioning support.
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        system_prompt: str,
        user_prompt: str,
        parameters: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ):
        """
        Initialize prompt template.
        
        Args:
            name: Template name
            version: Version string
            system_prompt: System prompt
            user_prompt: User prompt template
            parameters: Parameter definitions
            metadata: Additional metadata
        """
        self.name = name
        self.version = version
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.parameters = parameters or {}
        self.metadata = metadata or {
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'author': 'system',
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'system_prompt': self.system_prompt,
            'user_prompt': self.user_prompt,
            'parameters': self.parameters,
            'metadata': self.metadata,
        }
    
    def render(self, **kwargs) -> Dict[str, str]:
        """
        Render the prompt with provided parameters.
        
        Args:
            **kwargs: Parameter values
            
        Returns:
            Dictionary with system and user prompts
        """
        system_prompt = self.system_prompt
        user_prompt = self.user_prompt.format(**kwargs)
        
        return {
            'system': system_prompt,
            'user': user_prompt,
        }


class PromptVersioningService:
    """
    Service for managing prompt versions.
    
    Features:
    - Version tracking
    - Rollback support
    - A/B testing
    - Template management
    """
    
    def __init__(self):
        self._templates = {}
        self._cache = cache
    
    def register_template(
        self,
        name: str,
        version: str,
        system_prompt: str,
        user_prompt: str,
        parameters: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> PromptTemplate:
        """
        Register a new prompt template.
        
        Args:
            name: Template name
            version: Version string
            system_prompt: System prompt
            user_prompt: User prompt template
            parameters: Parameter definitions
            metadata: Additional metadata
            
        Returns:
            Registered PromptTemplate
        """
        template = PromptTemplate(
            name=name,
            version=version,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parameters=parameters,
            metadata=metadata,
        )
        
        # Store in cache
        cache_key = f"prompt_template:{name}:{version}"
        self._cache.set(cache_key, template.to_dict(), 86400)  # 24 hours
        
        # Update latest version
        latest_key = f"prompt_template:{name}:latest"
        self._cache.set(latest_key, version, 86400)
        
        self._templates[f"{name}:{version}"] = template
        
        logger.info(
            'Prompt template registered',
            name=name,
            version=version,
        )
        
        return template
    
    def get_template(self, name: str, version: Optional[str] = None) -> Optional[PromptTemplate]:
        """
        Get a prompt template by name and version.
        
        Args:
            name: Template name
            version: Version string (optional, defaults to latest)
            
        Returns:
            PromptTemplate or None
        """
        if version is None:
            # Get latest version
            latest_key = f"prompt_template:{name}:latest"
            version = self._cache.get(latest_key)
            if version is None:
                return None
        
        cache_key = f"prompt_template:{name}:{version}"
        template_dict = self._cache.get(cache_key)
        
        if template_dict:
            return PromptTemplate(
                name=template_dict['name'],
                version=template_dict['version'],
                system_prompt=template_dict['system_prompt'],
                user_prompt=template_dict['user_prompt'],
                parameters=template_dict.get('parameters', {}),
                metadata=template_dict.get('metadata', {}),
            )
        
        return None
    
    def list_templates(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List prompt templates.
        
        Args:
            name: Template name (optional)
            
        Returns:
            List of template information
        """
        templates = []
        
        # Get all templates from cache
        pattern = "prompt_template:*"
        # In production, use cache backend's keys() method
        
        return templates
    
    def rollback(self, name: str, to_version: str) -> bool:
        """
        Rollback to a previous version.
        
        Args:
            name: Template name
            to_version: Version to rollback to
            
        Returns:
            True if rollback succeeded
        """
        template = self.get_template(name, to_version)
        
        if template is None:
            logger.warning(
                'Template version not found for rollback',
                name=name,
                version=to_version,
            )
            return False
        
        # Update latest version
        latest_key = f"prompt_template:{name}:latest"
        self._cache.set(latest_key, to_version, 86400)
        
        logger.info(
            'Prompt template rolled back',
            name=name,
            to_version=to_version,
        )
        
        return True
    
    def create_ab_test(
        self,
        name: str,
        variations: List[str],
        weights: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Create an A/B test for prompt variations.
        
        Args:
            name: Base template name
            variations: List of version variations
            weights: Optional weights for each variation
            
        Returns:
            A/B test configuration
        """
        if weights is None:
            weights = [1.0 / len(variations)] * len(variations)
        
        ab_config = {
            'name': name,
            'variations': variations,
            'weights': weights,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
        }
        
        # Store in cache
        cache_key = f"prompt_ab_test:{name}"
        self._cache.set(cache_key, ab_config, 86400)
        
        return ab_config
    
    def get_ab_variation(self, name: str, user_id: str) -> Optional[str]:
        """
        Get A/B test variation for a user.
        
        Args:
            name: Template name
            user_id: User identifier
            
        Returns:
            Version variation or None
        """
        import hashlib
        
        cache_key = f"prompt_ab_test:{name}"
        ab_config = self._cache.get(cache_key)
        
        if ab_config is None:
            return None
        
        # Generate consistent hash for user
        hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest()[:8], 16)
        
        # Calculate cumulative weights
        cumulative = 0
        for variation, weight in zip(ab_config['variations'], ab_config['weights']):
            cumulative += weight
            if hash_value / 0xFFFFFFFF < cumulative:
                return variation
        
        return ab_config['variations'][-1]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get prompt versioning statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'type': 'prompt_versioning',
            'templates_count': len(self._templates),
            'cache_enabled': True,
            'cache_ttl_seconds': 86400,
        }


# ============================================================================
# Default Prompt Templates
# ============================================================================


DEFAULT_TEMPLATES = {
    'job_recommendation': {
        'v1': {
            'system': 'You are a helpful career assistant. Provide job recommendations based on the user\'s profile.',
            'user': 'User Profile:\n{profile}\n\nRecommend 5 jobs that match the user\'s skills and preferences.',
        },
        'v2': {
            'system': 'You are an expert career coach. Analyze the user\'s profile and provide tailored job recommendations with reasoning.',
            'user': 'User Profile:\n{profile}\n\nProvide 5 job recommendations with detailed reasoning for each match.',
        },
        'v3': {
            'system': 'You are a senior career advisor. Provide comprehensive job recommendations with skill gap analysis.',
            'user': 'User Profile:\n{profile}\n\nProvide 5 job recommendations with:\n1. Match score\n2. Required skills\n3. Skill gap analysis\n4. Learning recommendations',
        },
    },
    'career_advice': {
        'v1': {
            'system': 'You are a career advisor. Provide general career advice.',
            'user': 'User Question: {question}\n\nProvide career advice.',
        },
        'v2': {
            'system': 'You are an experienced career coach. Provide personalized career advice based on the user\'s background.',
            'user': 'User Background:\n{background}\n\nUser Question: {question}\n\nProvide personalized career advice.',
        },
    },
    'interview_preparation': {
        'v1': {
            'system': 'You are an interview coach. Help users prepare for interviews.',
            'user': 'Role: {role}\n\nGenerate 5 interview questions for this role.',
        },
        'v2': {
            'system': 'You are a senior interviewer. Generate comprehensive interview questions with expected answers.',
            'user': 'Role: {role}\n\nGenerate 5 interview questions with:\n1. Question\n2. Expected answer\n3. Evaluation criteria',
        },
    },
}


def load_default_templates(service: PromptVersioningService):
    """
    Load default prompt templates.
    
    Args:
        service: PromptVersioningService instance
    """
    for template_name, versions in DEFAULT_TEMPLATES.items():
        for version, template_data in versions.items():
            service.register_template(
                name=template_name,
                version=version,
                system_prompt=template_data['system'],
                user_prompt=template_data['user'],
                parameters={'role': 'string', 'profile': 'string', 'question': 'string', 'background': 'string'},
                metadata={'default': True},
            )