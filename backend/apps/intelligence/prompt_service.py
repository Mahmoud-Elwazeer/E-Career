"""
Prompt Service - Load prompts from database with fallbacks
"""
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from .models import PromptVersion

logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for loading and managing versioned prompts.

    Usage:
        prompt = prompt_service.get_prompt('cover_letter_generation', user_context={...})
    """

    CACHE_TTL = 300  # 5 minutes

    def get_prompt(
        self,
        name: str,
        variables: Optional[Dict[str, Any]] = None,
        fallback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load active prompt by name with template variable substitution.

        Args:
            name: Prompt identifier (e.g., 'cover_letter_generation')
            variables: Dict of variables to substitute in prompt template
            fallback: Fallback prompt text if DB lookup fails

        Returns:
            Dict with keys: content, system_prompt, model_target, max_tokens, temperature
        """
        cache_key = f"prompt:{name}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Prompt '{name}' loaded from cache")
            return self._substitute_variables(cached, variables)

        # Load from database
        try:
            prompt = PromptVersion.objects.filter(
                name=name,
                is_active=True
            ).first()

            if not prompt:
                logger.warning(f"No active prompt found for '{name}', using fallback")
                return self._fallback_response(fallback, variables)

            result = {
                'content': prompt.content,
                'system_prompt': prompt.system_prompt,
                'model_target': prompt.model_target,
                'max_tokens': prompt.max_tokens,
                'temperature': prompt.temperature,
                'prompt_id': str(prompt.id),
            }

            # Cache for 5 minutes
            cache.set(cache_key, result, self.CACHE_TTL)

            logger.info(f"Prompt '{name}' v{prompt.version} loaded from database")
            return self._substitute_variables(result, variables)

        except Exception as e:
            logger.error(f"Error loading prompt '{name}': {e}")
            return self._fallback_response(fallback, variables)

    def _substitute_variables(
        self,
        prompt_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Replace {variable} placeholders in prompt content."""
        if not variables:
            return prompt_data

        result = prompt_data.copy()
        try:
            result['content'] = prompt_data['content'].format(**variables)
            if prompt_data.get('system_prompt'):
                result['system_prompt'] = prompt_data['system_prompt'].format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable in prompt substitution: {e}")

        return result

    def _fallback_response(
        self,
        fallback: Optional[str],
        variables: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Return fallback prompt with default settings."""
        content = fallback or "Provide a helpful response."

        if variables:
            try:
                content = content.format(**variables)
            except KeyError:
                pass

        return {
            'content': content,
            'system_prompt': '',
            'model_target': 'haiku',
            'max_tokens': 1000,
            'temperature': 0.7,
            'prompt_id': None,
        }

    def invalidate_cache(self, name: str):
        """Clear cached prompt (call after updating in admin)."""
        cache_key = f"prompt:{name}"
        cache.delete(cache_key)
        logger.info(f"Cache invalidated for prompt '{name}'")


# Global instance
prompt_service = PromptService()
