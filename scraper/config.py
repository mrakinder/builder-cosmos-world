"""
Configuration module for OLX scraper
====================================

Manages all configuration settings, URLs, and environment variables.
"""

import os
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ScraperConfig:
    """Configuration class for OLX scraper settings"""
    
    # Base URLs for different scraping modes
    BASE_URLS = {
        "sale": "https://www.olx.ua/nedvizhimost/kvartiry/prodazha/ivanofrankovsk/",
        "rent": "https://www.olx.ua/nedvizhimost/kvartiry/arenda/ivanofrankovsk/"
    }
    
    # Browser and scraping settings
    HEADLESS: bool = True
    USER_AGENT_ROTATION: bool = True
    ENABLE_STEALTH: bool = True
    BLOCK_IMAGES: bool = True  # Faster loading
    BLOCK_CSS: bool = False    # Keep CSS for proper selectors
    
    # Timing and retry settings
    BASE_DELAY_MS: int = 1500
    MAX_DELAY_MS: int = 4000
    RETRY_ATTEMPTS: int = 5
    RETRY_DELAY: float = 2.0
    PAGE_TIMEOUT: int = 30000
    ELEMENT_TIMEOUT: int = 10000
    
    # Data persistence settings
    DATABASE_PATH: str = "data/olx_offers.sqlite"
    EXPORT_PATH: str = "data/exports/olx_offers_latest.csv"
    LOGS_PATH: str = "scraper/logs"
    
    # Scraping limits
    DEFAULT_MAX_PAGES: int = 10
    MAX_ITEMS_PER_PAGE: int = 50
    
    # Target city and location settings
    TARGET_CITY: str = "Івано-Франківськ"
    TARGET_CURRENCY: str = "USD"
    
    def __post_init__(self):
        """Create necessary directories"""
        os.makedirs(Path(self.DATABASE_PATH).parent, exist_ok=True)
        os.makedirs(Path(self.EXPORT_PATH).parent, exist_ok=True)
        os.makedirs(self.LOGS_PATH, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        """Create config from environment variables"""
        return cls(
            HEADLESS=os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true',
            BASE_DELAY_MS=int(os.getenv('SCRAPER_DELAY_MS', '1500')),
            MAX_DELAY_MS=int(os.getenv('SCRAPER_MAX_DELAY_MS', '4000')),
            RETRY_ATTEMPTS=int(os.getenv('SCRAPER_RETRY_ATTEMPTS', '5')),
            DATABASE_PATH=os.getenv('SCRAPER_DB_PATH', 'data/olx_offers.sqlite'),
            EXPORT_PATH=os.getenv('SCRAPER_EXPORT_PATH', 'data/exports/olx_offers_latest.csv'),
            DEFAULT_MAX_PAGES=int(os.getenv('SCRAPER_MAX_PAGES', '10'))
        )

# CSS Selectors for OLX elements
class OLXSelectors:
    """CSS selectors for OLX website elements"""
    
    # Listing page selectors
    LISTING_CONTAINER = '[data-cy="l-card"]'
    LISTING_LINK = 'a[data-cy="listing-ad-title"]'
    LISTING_TITLE = '[data-cy="listing-ad-title"]'
    LISTING_PRICE = '[data-testid="ad-price"]'
    LISTING_LOCATION = '[data-testid="location-date"]'
    
    # Individual ad page selectors  
    AD_TITLE = 'h1[data-cy="ad_title"]'
    AD_PRICE = '[data-testid="ad-price-container"]'
    AD_DESCRIPTION = '[data-cy="ad_description"] div'
    AD_PARAMETERS = '[data-testid="parameters-container"]'
    AD_LOCATION = '[data-cy="ad-location"]'
    AD_ID = '[data-cy="ad-id"]'
    
    # Seller information
    SELLER_NAME = '[data-cy="seller_card"] h4'
    SELLER_TYPE = '[data-cy="seller_card"] .css-1kn2r8g'
    
    # Pagination
    NEXT_PAGE = '[data-testid="pagination-forward"]'
    PAGE_NUMBER = '[data-testid="pagination-list"] button[aria-current="page"]'

# Street to District mapping for Ivano-Frankivsk
STREET_DISTRICT_MAPPING = {
    # Центр
    "Галицька": "Центр",
    "Незалежності": "Центр", 
    "Грушевського": "Центр",
    "Січових Стрільців": "Центр",
    "Шевченка": "Центр",
    "Леся Курбаса": "Центр",
    "Чорновола": "Центр",
    "Василіянок": "Центр",
    
    # Пасічна
    "Тролейбусна": "Пасічна",
    "Пасічна": "Пасічна",
    "Федьковича": "Пасічна",
    "Бандери": "Пасічна",
    
    # БАМ
    "Івасюка": "БАМ",
    "Надрічна": "БАМ",
    "Вовчинецька": "БАМ",
    "Мазепи": "БАМ",
    
    # Каскад
    "24 Серпня": "Каскад",
    "Каскадна": "Каскад",
    "Короля Данила": "Каскад",
    "Хмельницького": "Каскад",
    
    # Залізничний (Вокзал)
    "Стефаника": "Залізничний (Вокзал)",
    "Привокзальна": "Залізничний (Вокзал)",
    "Залізнична": "Залізничний (В��кзал)",
    "Коновальця": "Залізничний (Вокзал)",
    
    # Брати
    "Хоткевича": "Брати",
    "Миколайчука": "Брати", 
    "Довга": "Брати",
    "Є. Коновальця": "Брати",
    
    # Софіївка
    "Пстрака": "Софіївка",
    "Софійська": "Софіївка",
    "Левицького": "Софіївка",
    "Пулюя": "Софіївка",
    
    # Будівельників
    "Селянська": "Будівельників",
    "Будівельників": "Будівельників",
    "Промислова": "Будівельників",
    "Автомобільна": "Будівельників",
    
    # Набережна
    "Набережна ім. В. Стефаника": "Набережна",
    "Набережна": "Набережна", 
    "Дністровська": "Набережна",
    "Мільйонна": "Набережна",
    
    # Опришівці
    "Опришівська": "Опришівці",
    "Гуцульська": "Опришівці",
    "Карпатська": "Опришівці",
    "Покутська": "Опришівц��"
}

# Default scraper configuration instance
config = ScraperConfig.from_env()
