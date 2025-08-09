"""
Botasaurus OLX Scraper Module
Module 1: Anti-detection web scraping for Ivano-Frankivsk real estate
"""

from .olx_scraper import BotasaurusOLXScraper, run_scraper, Property
from .config import ScrapingConfig, DISTRICTS, STREET_TO_DISTRICT
from .classify import classify_seller, get_classification_confidence
from .persist import DatabaseManager
from .utils import Logger, extract_price, extract_area, clean_text

__all__ = [
    'BotasaurusOLXScraper',
    'run_scraper',
    'Property',
    'ScrapingConfig',
    'DISTRICTS',
    'STREET_TO_DISTRICT',
    'classify_seller',
    'get_classification_confidence',
    'DatabaseManager',
    'Logger',
    'extract_price',
    'extract_area',
    'clean_text'
]

__version__ = "1.0.0"
__author__ = "Property Monitor IF Team"
__description__ = "Anti-detection OLX scraper for Ivano-Frankivsk real estate using Botasaurus framework"
