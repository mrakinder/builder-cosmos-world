"""
Utility functions for the OLX scraper
====================================

Helper functions for delays, retries, data normalization, and other utilities.
"""

import re
import time
import random
import logging
from typing import Optional, List, Any, Union
from functools import wraps
from fake_useragent import UserAgent
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class UserAgentRotator:
    """Manages user agent rotation for requests"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.used_agents = []
        self.max_used = 10  # Keep track of last 10 used agents
    
    def get_random_agent(self) -> str:
        """Get a random user agent"""
        try:
            agent = self.ua.random
            
            # Avoid recently used agents
            attempts = 0
            while agent in self.used_agents and attempts < 5:
                agent = self.ua.random
                attempts += 1
            
            # Update used agents list
            self.used_agents.append(agent)
            if len(self.used_agents) > self.max_used:
                self.used_agents.pop(0)
            
            return agent
        except Exception:
            # Fallback user agent
            return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    def get_chrome_agent(self) -> str:
        """Get a Chrome user agent specifically"""
        try:
            return self.ua.chrome
        except Exception:
            return self.get_random_agent()

def human_delay(min_seconds: float = 1.5, max_seconds: float = 4.0) -> None:
    """
    Create a human-like delay with random timing
    
    Args:
        min_seconds: Minimum delay time
        max_seconds: Maximum delay time
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def progressive_delay(attempt: int, base_delay: float = 2.0, max_delay: float = 30.0) -> None:
    """
    Create progressive delay for retries (exponential backoff)
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay time
        max_delay: Maximum delay time
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add some randomness
    delay *= random.uniform(0.8, 1.2)
    logger.debug(f"Progressive delay (attempt {attempt + 1}): {delay:.2f} seconds")
    time.sleep(delay)

def normalize_number(text: str) -> Optional[float]:
    """
    Extract and normalize a number from text
    
    Args:
        text: Text containing a number
        
    Returns:
        Normalized float number or None
    """
    if not text:
        return None
    
    # Remove spaces and common separators
    cleaned = re.sub(r'[^\d,.]', '', str(text))
    
    if not cleaned:
        return None
    
    # Handle Ukrainian decimal notation (comma as decimal separator)
    if ',' in cleaned and '.' in cleaned:
        # If both comma and dot, assume dot is thousand separator
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        # Only comma - treat as decimal separator
        cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not normalize number: {text}")
        return None

def extract_currency(text: str) -> str:
    """
    Extract currency from price text
    
    Args:
        text: Text containing price and currency
        
    Returns:
        Currency code (USD, UAH, EUR, etc.)
    """
    if not text:
        return 'USD'
    
    text_lower = text.lower()
    
    # Ukrainian hryvnia
    if any(symbol in text_lower for symbol in ['грн', '₴', 'uah', 'гривн']):
        return 'UAH'
    
    # US Dollar  
    if any(symbol in text_lower for symbol in ['$', 'usd', 'долар', 'dollar']):
        return 'USD'
    
    # Euro
    if any(symbol in text_lower for symbol in ['€', 'eur', 'евро', 'euro']):
        return 'EUR'
    
    # Default to USD if not specified
    return 'USD'

def safe_extract_text(element: Union[WebElement, None]) -> str:
    """
    Safely extract text from a WebElement
    
    Args:
        element: Selenium WebElement or None
        
    Returns:
        Extracted text or empty string
    """
    if element is None:
        return ""
    
    try:
        text = element.text
        if text:
            return text.strip()
        
        # Fallback to innerHTML if text is empty
        text = element.get_attribute('innerHTML')
        if text:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            return text.strip()
        
        return ""
    except WebDriverException:
        return ""

def safe_extract_attribute(element: Union[WebElement, None], attribute: str) -> str:
    """
    Safely extract an attribute from a WebElement
    
    Args:
        element: Selenium WebElement or None
        attribute: Attribute name to extract
        
    Returns:
        Attribute value or empty string
    """
    if element is None:
        return ""
    
    try:
        value = element.get_attribute(attribute)
        return value.strip() if value else ""
    except WebDriverException:
        return ""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
def retry_on_failure(func):
    """
    Decorator for retrying functions on failure
    
    Args:
        func: Function to retry
        
    Returns:
        Decorated function with retry logic
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters (keep Ukrainian characters)
    text = re.sub(r'[^\w\s\-.,!?()\u0400-\u04FF]', '', text)
    
    return text.strip()

def validate_url(url: str) -> bool:
    """
    Validate if URL is a proper OLX property URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid OLX property URL
    """
    if not url:
        return False
    
    # Must be OLX domain
    if 'olx.ua' not in url:
        return False
    
    # Must be a property listing (contains /d/)
    if '/d/' not in url:
        return False
    
    # Must be HTTPS
    if not url.startswith('https://'):
        return False
    
    return True

def format_price(price: Optional[float], currency: str = 'USD') -> str:
    """
    Format price for display
    
    Args:
        price: Price value
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    if price is None:
        return "Ціна не вказана"
    
    if currency == 'USD':
        return f"${price:,.0f}"
    elif currency == 'UAH':
        return f"{price:,.0f} грн"
    elif currency == 'EUR':
        return f"€{price:,.0f}"
    else:
        return f"{price:,.0f} {currency}"

def extract_rooms_from_text(text: str) -> Optional[int]:
    """
    Extract number of rooms from text
    
    Args:
        text: Text that may contain room information
        
    Returns:
        Number of rooms or None
    """
    if not text:
        return None
    
    # Common patterns for room numbers
    patterns = [
        r'(\d+)[\s-]*кімн',  # "2-кімн", "2 кімн"
        r'(\d+)[\s-]*к\.',   # "2-к.", "2 к."
        r'(\d+)[\s-]*room',  # "2-room", "2 room"
        r'(\d+)r\b',         # "2r"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                rooms = int(match.group(1))
                if 1 <= rooms <= 10:  # Reasonable range
                    return rooms
            except ValueError:
                continue
    
    return None

def generate_session_id() -> str:
    """Generate a unique session ID for tracking"""
    import uuid
    return str(uuid.uuid4())[:8]

def log_performance_metrics(func):
    """Decorator to log performance metrics for functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {str(e)}")
            raise
    return wrapper
