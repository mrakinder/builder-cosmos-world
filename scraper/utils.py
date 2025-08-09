"""
Utility functions for OLX scraper
"""

import re
import logging
from typing import Optional, Tuple
from datetime import datetime
import os


class Logger:
    """Custom logger for scraper"""
    
    def __init__(self, log_file: str, level: str = "INFO"):
        self.logger = logging.getLogger("botasaurus_scraper")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create logs directory if not exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


def extract_price(price_text: str) -> Tuple[Optional[float], str]:
    """
    Extract price and currency from price text
    
    Args:
        price_text: Raw price text from OLX
        
    Returns:
        Tuple[Optional[float], str]: (price_value, currency)
    """
    if not price_text:
        return None, ""
    
    # Clean text
    price_text = price_text.replace(',', '').replace(' ', '')
    
    # Extract number
    price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
    if not price_match:
        return None, ""
    
    price_value = float(price_match.group(1))
    
    # Determine currency
    if any(currency in price_text.upper() for currency in ['USD', '$', 'DOLLAR']):
        return price_value, "USD"
    elif any(currency in price_text.upper() for currency in ['EUR', '€', 'EURO']):
        return price_value, "EUR"
    elif any(currency in price_text.upper() for currency in ['UAH', '₴', 'ГРН']):
        return price_value, "UAH"
    else:
        # Default to USD if unclear
        return price_value, "USD"


def extract_area(text: str) -> Optional[float]:
    """
    Extract area in square meters from text
    
    Args:
        text: Text to search for area
        
    Returns:
        Optional[float]: Area in square meters or None
    """
    if not text:
        return None
    
    # Common area patterns
    area_patterns = [
        r'(\d+(?:\.\d+)?)\s*м²',
        r'(\d+(?:\.\d+)?)\s*кв\.?\s*м',
        r'(\d+(?:\.\d+)?)\s*sq\.?\s*m',
        r'(\d+(?:\.\d+)?)\s*м\s*кв',
        r'площа\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*метр'
    ]
    
    for pattern in area_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            area_value = float(match.group(1))
            # Sanity check (reasonable apartment sizes)
            if 10 <= area_value <= 500:
                return area_value
    
    return None


def extract_rooms(text: str) -> Optional[int]:
    """
    Extract number of rooms from text
    
    Args:
        text: Text to search for room count
        
    Returns:
        Optional[int]: Number of rooms or None
    """
    if not text:
        return None
    
    room_patterns = [
        r'(\d+)\s*кімн',
        r'(\d+)\s*к\.',
        r'(\d+)\s*комн',
        r'(\d+)\s*room',
        r'(\d+)\s*спальн'
    ]
    
    for pattern in room_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rooms = int(match.group(1))
            # Sanity check (1-10 rooms)
            if 1 <= rooms <= 10:
                return rooms
    
    return None


def extract_floor(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract floor and total floors from text
    
    Args:
        text: Text to search for floor info
        
    Returns:
        Tuple[Optional[int], Optional[int]]: (floor, total_floors)
    """
    if not text:
        return None, None
    
    # Pattern: "5/9 поверх" or "5 из 9" or "5th floor of 9"
    floor_patterns = [
        r'(\d+)\s*/\s*(\d+)\s*поверх',
        r'(\d+)\s*из\s*(\d+)',
        r'(\d+)\s*of\s*(\d+)\s*floor',
        r'(\d+)\s*/\s*(\d+)\s*эт',
        r'поверх\s*(\d+)\s*/\s*(\d+)'
    ]
    
    for pattern in floor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            floor = int(match.group(1))
            total_floors = int(match.group(2))
            
            # Sanity check
            if 1 <= floor <= total_floors <= 50:
                return floor, total_floors
    
    # Single floor pattern
    single_floor_patterns = [
        r'(\d+)\s*поверх',
        r'(\d+)\s*этаж',
        r'floor\s*(\d+)'
    ]
    
    for pattern in single_floor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            floor = int(match.group(1))
            if 1 <= floor <= 50:
                return floor, None
    
    return None, None


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters but keep Ukrainian letters
    text = re.sub(r'[^\w\s\u0400-\u04FF.,!?()-]', '', text)
    
    return text


def format_currency(amount: float, currency: str) -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Numeric amount
        currency: Currency code
        
    Returns:
        str: Formatted currency string
    """
    if currency == "USD":
        return f"${amount:,.0f}"
    elif currency == "EUR":
        return f"€{amount:,.0f}"
    elif currency == "UAH":
        return f"₴{amount:,.0f}"
    else:
        return f"{amount:,.0f} {currency}"


def validate_property_data(property_dict: dict) -> dict:
    """
    Validate and clean property data
    
    Args:
        property_dict: Property data dictionary
        
    Returns:
        dict: Validated property data
    """
    # Ensure required fields
    required_fields = ['olx_id', 'title', 'listing_url']
    for field in required_fields:
        if not property_dict.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate numeric fields
    if property_dict.get('price_usd'):
        price = float(property_dict['price_usd'])
        if price <= 0 or price > 10_000_000:  # Reasonable price range
            property_dict['price_usd'] = None
    
    if property_dict.get('area'):
        area = float(property_dict['area'])
        if area <= 0 or area > 1000:  # Reasonable area range
            property_dict['area'] = None
    
    if property_dict.get('rooms'):
        rooms = int(property_dict['rooms'])
        if rooms <= 0 or rooms > 20:
            property_dict['rooms'] = None
    
    if property_dict.get('floor'):
        floor = int(property_dict['floor'])
        if floor <= 0 or floor > 100:
            property_dict['floor'] = None
    
    return property_dict


def detect_building_type(title: str, description: str = "") -> Optional[str]:
    """
    Detect building type from title and description
    
    Args:
        title: Property title
        description: Property description
        
    Returns:
        Optional[str]: Building type or None
    """
    text = (title + " " + description).lower()
    
    building_types = {
        'новобудова': ['новобудова', 'новострой', 'новостройка', 'new building'],
        'вторинка': ['вторинка', 'вторичка', 'вторичное жилье', 'secondary'],
        'котедж': ['котедж', 'коттедж', 'house', 'будинок', 'дом'],
        'таунхаус': ['таунхаус', 'townhouse', 'таун-хаус'],
        'квартира': ['квартира', 'apartment', 'кв.', 'кварт.']
    }
    
    for building_type, keywords in building_types.items():
        for keyword in keywords:
            if keyword in text:
                return building_type
    
    return 'квартира'  # Default


def detect_renovation_status(title: str, description: str = "") -> Optional[str]:
    """
    Detect renovation status from title and description
    
    Args:
        title: Property title
        description: Property description
        
    Returns:
        Optional[str]: Renovation status or None
    """
    text = (title + " " + description).lower()
    
    renovation_statuses = {
        'євроремонт': ['євроремонт', 'евроремонт', 'euro renovation'],
        'дизайнерський': ['дизайнерський', 'дизайнерский', 'design renovation'],
        'відмінний': ['відмінний', 'отличный', 'excellent'],
        'хороший': ['хороший', 'good', 'добрий'],
        'косметичний': ['косметичний', 'косметический', 'cosmetic'],
        'потребує ремонту': ['потребує ремонт', 'требует ремонт', 'needs repair', 'під ремонт']
    }
    
    for status, keywords in renovation_statuses.items():
        for keyword in keywords:
            if keyword in text:
                return status
    
    return None
