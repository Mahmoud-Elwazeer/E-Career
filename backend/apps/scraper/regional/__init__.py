"""Regional job boards scrapers package."""
from .jobspy_wrapper import scrape_bayt, scrape_wuzzuf, scrape_gulftalent

__all__ = [
    'scrape_bayt',
    'scrape_wuzzuf',
    'scrape_gulftalent',
]