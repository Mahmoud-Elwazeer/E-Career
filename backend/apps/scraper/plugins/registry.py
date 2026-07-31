"""
Scraper Plugin Registry

Manages registration and lookup of scraper plugins.
"""
from typing import Dict, Optional, Type
from .interface import ScraperPlugin, BaseScraperPlugin


class ScraperPluginRegistry:
    """
    Registry for scraper plugins.
    
    Provides methods to register, unregister, and look up scraper plugins.
    """
    
    def __init__(self):
        self._plugins: Dict[str, Type[ScraperPlugin]] = {}
        self._instances: Dict[str, ScraperPlugin] = {}
    
    def register(self, platform: str, scraper_class: Type[ScraperPlugin]) -> None:
        """
        Register a scraper plugin for a platform.
        
        Args:
            platform: Platform name (e.g., 'greenhouse')
            scraper_class: Scraper plugin class
        """
        self._plugins[platform.lower()] = scraper_class
    
    def unregister(self, platform: str) -> bool:
        """
        Unregister a scraper plugin.
        
        Args:
            platform: Platform name
            
        Returns:
            True if unregistered, False if not found
        """
        if platform.lower() in self._plugins:
            del self._plugins[platform.lower()]
            return True
        return False
    
    def get_scraper(self, platform: str, company_slug: str) -> Optional[ScraperPlugin]:
        """
        Get a scraper instance for a platform.
        
        Args:
            platform: Platform name
            company_slug: Company slug/identifier
            
        Returns:
            ScraperPlugin instance or None if platform not found
        """
        platform_lower = platform.lower()
        
        # Check cache first
        cache_key = f"{platform_lower}:{company_slug}"
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        # Get class from registry
        scraper_class = self._plugins.get(platform_lower)
        if not scraper_class:
            return None
        
        # Create instance
        scraper = scraper_class(company_slug)
        self._instances[cache_key] = scraper
        
        return scraper
    
    def get_all_platforms(self) -> list:
        """
        Get all registered platform names.
        
        Returns:
            List of platform names
        """
        return list(self._plugins.keys())
    
    def get_scraper_class(self, platform: str) -> Optional[Type[ScraperPlugin]]:
        """
        Get the scraper class for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            ScraperPlugin class or None if not found
        """
        return self._plugins.get(platform.lower())
    
    def clear_cache(self) -> None:
        """Clear the instance cache."""
        self._instances.clear()


# Global plugin registry instance
plugin_registry = ScraperPluginRegistry()


def register_all_scrapers() -> None:
    """
    Register all available scrapers.
    
    This function should be called during application startup.
    """
    from apps.scraper.ats import (
        GreenhouseScraper, LeverScraper, AshbyScraper, 
        BambooHRScraper, WorkdayScraper,
        SmartRecruitersScraper, WorkableScraper, TeamtailorScraper,
    )
    
    # Register ATS scrapers
    plugin_registry.register('greenhouse', GreenhouseScraper)
    plugin_registry.register('lever', LeverScraper)
    plugin_registry.register('ashby', AshbyScraper)
    plugin_registry.register('bamboohr', BambooHRScraper)
    plugin_registry.register('workday', WorkdayScraper)
    plugin_registry.register('smartrecruiters', SmartRecruitersScraper)
    plugin_registry.register('workable', WorkableScraper)
    plugin_registry.register('teamtailor', TeamtailorScraper)


# Register all scrapers on import
register_all_scrapers()