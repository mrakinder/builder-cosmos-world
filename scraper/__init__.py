"""
OLX Real Estate Scraper for Ivano-Frankivsk
============================================

A comprehensive scraping solution using Botasaurus framework for collecting
real estate data from OLX with anti-detection, retry logic, and data persistence.

Modules:
    - config: Configuration and settings management
    - olx_scraper: Main scraper implementation with Botasaurus
    - parsing: HTML parsing and data extraction
    - classify: Seller type classification (owner vs agency)
    - persist: SQLite storage and CSV export
    - utils: Utilities for delays, retries, and user-agent rotation
"""

__version__ = "1.0.0"
__author__ = "Glow Nest XGB Team"

from .config import ScraperConfig
from .olx_scraper import OLXScraper
from .parsing import PropertyParser
from .classify import SellerClassifier
from .persist import DataPersistence

__all__ = [
    "ScraperConfig",
    "OLXScraper", 
    "PropertyParser",
    "SellerClassifier",
    "DataPersistence"
]
