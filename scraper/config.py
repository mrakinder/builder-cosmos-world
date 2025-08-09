"""
Configuration for Botasaurus OLX Scraper
Module 1: Anti-detection web scraping for Ivano-Frankivsk real estate
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ScrapingConfig:
    """Configuration class for OLX scraping with Botasaurus"""
    
    # Base URLs and search parameters
    BASE_URL: str = "https://www.olx.ua"
    CITY_URL: str = "https://www.olx.ua/d/uk/nedvizhimost/kvartiry/ivano-frankivsk/"
    
    # Scraping behavior
    MAX_PAGES: int = int(os.getenv("SCRAPER_MAX_PAGES", 50))
    DELAY_MS: int = int(os.getenv("SCRAPER_DELAY_MS", 5000))
    HEADFUL: bool = os.getenv("SCRAPER_HEADFUL", "false").lower() == "true"
    PROXY_ENABLED: bool = os.getenv("SCRAPER_PROXY_ENABLED", "false").lower() == "true"
    
    # Anti-detection settings
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    
    # Request headers
    HEADERS: Dict[str, str] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Search filters
    PROPERTY_TYPES: List[str] = ["kvartiry"]  # apartments
    LISTING_TYPES: List[str] = ["rent", "sale"]  # оренда, продаж
    CURRENCY_FILTER: str = "USD"  # Only USD listings
    
    # Selectors for parsing
    SELECTORS = {
        "listing_container": "[data-cy='l-card']",
        "title": "h6[data-cy='l-card-title']",
        "price": "[data-testid='ad-price']",
        "location": "[data-cy='l-card-location']", 
        "details": "[data-cy='l-card-details']",
        "seller_info": "[data-cy='seller-info']",
        "link": "a[data-cy='l-card-link']",
        "image": "img[data-cy='l-card-image']",
        "date": "[data-cy='l-card-date']",
        "promoted": "[data-cy='promoted-badge']"
    }
    
    # Database settings
    DB_URL: str = os.getenv("DB_URL", "sqlite:///data/olx_offers.sqlite")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "scraper/logs/botasaurus_scraper.log"
    
    # Output settings
    EXPORT_CSV: bool = True
    CSV_PATH: str = "data/exports/olx_offers_latest.csv"
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 10  # seconds
    
    # Anti-ban settings
    MIN_DELAY: int = 4000  # ms
    MAX_DELAY: int = 8000  # ms
    RANDOM_VIEWPORT: bool = True
    ROTATE_USER_AGENT: bool = True
    
    # Street to district mapping
    STREETS_MAPPING_FILE: str = os.getenv("STREET_MAPPING_FILE", "districts/streets_mapping.csv")
    DEFAULT_DISTRICT: str = os.getenv("DEFAULT_DISTRICT", "Центр")

# Ivano-Frankivsk districts
DISTRICTS = [
    "Центр",
    "Пасічна", 
    "БАМ",
    "Каскад",
    "Залізничний (Вокзал)",
    "Брати",
    "Софіївка",
    "Будівельників",
    "Набережна",
    "Опришівці"
]

# Street to district mapping for Ivano-Frankivsk
STREET_TO_DISTRICT = {
    # Центр
    "Августина Волошина": "Центр",
    "Арсенальна": "Центр",
    "Вічева": "Центр",
    "Галицька": "Центр",
    "Гетьмана Мазепи": "Центр",
    "Грушевського": "Центр",
    "Данила Галицького": "Центр",
    "Дністровська": "Центр",
    "Європейська": "Центр",
    "Євгена Коновальця": "Центр",
    "Січових Стрільців": "Центр",
    "Шевченка": "Центр",
    "Незалежності": "Центр",
    "Леся Курбаса": "Центр",
    "Мазепи": "Центр",
    "Міцкевича": "Центр",
    "Курбаса": "Центр",
    
    # Пасічна
    "Пасічна": "Пасічна",
    "Старопасічна": "Пасічна",
    "Пасічна Нова": "Пасічна",
    "Пасічний провулок": "Пасічна",
    "Трускавецька": "Пасічна",
    "Промислова": "Пасічна",
    "Зелена": "Пасічна",
    
    # БАМ
    "Північна": "БАМ",
    "Відінська": "БАМ", 
    "БАМ": "БАМ",
    "Богдана Хмельницького": "БАМ",
    "Будівельна": "БАМ",
    "Молодіжна": "БАМ",
    "Польова": "БАМ",
    
    # Каскад
    "Каскадна": "Каскад",
    "Тисменицька": "Каскад",
    "Вишнева": "Каскад",
    "Ярослава Мудрого": "Каскад",
    "Пушкіна": "Каскад",
    "Лермонтова": "Каскад",
    
    # Залізничний (Вокзал)
    "Залізнична": "Залізничний (Вокзал)",
    "Привокзальна": "Залізничний (Вокзал)",
    "Вокзальна": "Залізничний (Вокзал)",
    "Станційна": "Залізничний (Вокзал)",
    "Перонна": "Залізничний (Вокзал)",
    
    # Брати
    "Братів Бойчуків": "Брати",
    "Братів Рогатинців": "Брати",
    "Чорновола": "Брати",
    "Стуса": "Брати",
    "Антоновича": "Брати",
    
    # Софіївка
    "Софіївська": "Софіївка",
    "Академіка Сахарова": "Софіївка",
    "Сахарова": "Софіївка",
    "Надбережна": "Софіївка",
    "Набережна Стефаника": "Софіївка",
    
    # Будівельників
    "Будівельників": "Будівельників",
    "Конструкторська": "Будівельників",
    "Робітнича": "Будівельників",
    "Енергетична": "Будівельників",
    "Монтажна": "Будівельників",
    
    # Набережна
    "Набережна": "Набережна",
    "Набережна Стефаника": "Набережна",
    "Річна": "Набережна",
    "Прибережна": "Набе��ежна",
    
    # Опришівці
    "Опришівська": "Опришівці",
    "Довбуша": "Опришівці",
    "Карпатська": "Опришівці",
    "Гуцульська": "Опришівці"
}

# Owner/agency classification keywords
OWNER_KEYWORDS = [
    "власник", "власниця", "від власника", "без посередників",
    "приватна особа", "безпосередньо", "хазяїн", "хазяйка",
    "особисто", "прямий продаж", "без агентства", "без комісії"
]

AGENCY_KEYWORDS = [
    "агентство", "ріелтор", "нерухомість", "estate", "reality",
    "девелопер", "забудовник", "компанія", "ТОВ", "ПП", "фірма",
    "центр нерухомості", "операції з нерухомістю", "професійний ріелтор"
]
