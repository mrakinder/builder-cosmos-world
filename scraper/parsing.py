"""
HTML parsing and data extraction module
======================================

Extracts property data from OLX HTML pages with robust selectors and fallbacks.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .models import PropertyData
from .config import OLXSelectors, STREET_DISTRICT_MAPPING
from .utils import normalize_number, extract_currency, safe_extract_text

logger = logging.getLogger(__name__)

class PropertyParser:
    """Parser for extracting property data from OLX pages"""
    
    def __init__(self):
        self.selectors = OLXSelectors()
        self.street_mapping = STREET_DISTRICT_MAPPING
    
    def parse_listing_page(self, driver) -> List[str]:
        """
        Extract URLs from a listing page
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            List of property URLs found on the page
        """
        property_urls = []
        
        try:
            # Find all property cards
            listings = driver.find_elements(By.CSS_SELECTOR, self.selectors.LISTING_CONTAINER)
            logger.info(f"Found {len(listings)} property listings on page")
            
            for listing in listings:
                try:
                    # Extract URL from listing
                    link_element = listing.find_element(By.CSS_SELECTOR, self.selectors.LISTING_LINK)
                    url = link_element.get_attribute('href')
                    
                    if url and '/d/' in url:  # Valid OLX property URL
                        property_urls.append(url)
                        
                except NoSuchElementException:
                    logger.warning("Could not extract URL from listing")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing listing page: {str(e)}")
        
        logger.info(f"Extracted {len(property_urls)} property URLs")
        return property_urls
    
    def parse_property_page(self, driver, url: str) -> Optional[PropertyData]:
        """
        Parse individual property page and extract all data
        
        Args:
            driver: Selenium WebDriver instance
            url: Property page URL
            
        Returns:
            PropertyData object or None if parsing failed
        """
        try:
            # Extract ad ID from URL
            ad_id = self._extract_ad_id(url)
            if not ad_id:
                logger.error(f"Could not extract ad_id from URL: {url}")
                return None
            
            # Extract basic information
            title = self._extract_title(driver)
            price_data = self._extract_price(driver)
            location_data = self._extract_location(driver)
            description = self._extract_description(driver)
            
            # Extract property parameters
            params = self._extract_parameters(driver)
            
            # Extract seller information
            seller_data = self._extract_seller_info(driver)
            
            # Determine district from street mapping
            district_info = self._determine_district(location_data.get('text', ''), description)
            
            # Create PropertyData object
            property_data = PropertyData(
                ad_id=ad_id,
                title=title,
                url=url,
                price_value=price_data.get('value'),
                price_currency=price_data.get('currency', 'USD'),
                location_city=location_data.get('city', 'Івано-Франківськ'),
                location_text=location_data.get('text', ''),
                district=district_info.get('district'),
                street=district_info.get('street'),
                rooms=params.get('rooms'),
                area_total=params.get('area'),
                floor=params.get('floor'),
                floors_total=params.get('floors_total'),
                building_type=params.get('building_type'),
                renovation=params.get('renovation'),
                description=description,
                seller_type=seller_data.get('type', 'unknown'),
                seller_name=seller_data.get('name'),
                seller_signals=seller_data.get('signals', {}),
                district_source=district_info.get('source', 'unknown')
            )
            
            logger.info(f"Successfully parsed property: {ad_id}")
            return property_data
            
        except Exception as e:
            logger.error(f"Error parsing property page {url}: {str(e)}")
            return None
    
    def _extract_ad_id(self, url: str) -> Optional[str]:
        """Extract ad ID from OLX URL"""
        # OLX URLs format: https://www.olx.ua/.../ad-name-ID*.html
        match = re.search(r'-ID([A-Za-z0-9]+)', url)
        if match:
            return match.group(1)
        
        # Alternative: extract from end of URL
        match = re.search(r'/([A-Za-z0-9]+)\.html$', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_title(self, driver) -> str:
        """Extract property title"""
        try:
            element = driver.find_element(By.CSS_SELECTOR, self.selectors.AD_TITLE)
            return safe_extract_text(element).strip()
        except NoSuchElementException:
            # Fallback to page title
            try:
                return driver.title.split(' - ')[0].strip()
            except:
                return "Без назви"
    
    def _extract_price(self, driver) -> Dict[str, Any]:
        """Extract price information"""
        price_data = {'value': None, 'currency': 'USD'}
        
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, self.selectors.AD_PRICE)
            price_text = safe_extract_text(price_element)
            
            # Extract currency
            currency = extract_currency(price_text)
            if currency:
                price_data['currency'] = currency
            
            # Extract numeric value
            price_value = normalize_number(price_text)
            price_data['value'] = price_value
            
        except NoSuchElementException:
            logger.warning("Could not find price element")
        
        return price_data
    
    def _extract_location(self, driver) -> Dict[str, str]:
        """Extract location information"""
        location_data = {'city': 'Івано-Франківськ', 'text': ''}
        
        try:
            location_element = driver.find_element(By.CSS_SELECTOR, self.selectors.AD_LOCATION)
            location_text = safe_extract_text(location_element)
            
            location_data['text'] = location_text
            
            # Extract city if different
            if 'Івано-Франківськ' not in location_text:
                city_match = re.search(r'([А-Яа-яЁёІіЇїЄє\-\s]+),\s*[А-Яа-яЁёІіЇїЄє]', location_text)
                if city_match:
                    location_data['city'] = city_match.group(1).strip()
                    
        except NoSuchElementException:
            logger.warning("Could not find location element")
        
        return location_data
    
    def _extract_description(self, driver) -> str:
        """Extract property description"""
        try:
            desc_element = driver.find_element(By.CSS_SELECTOR, self.selectors.AD_DESCRIPTION)
            return safe_extract_text(desc_element).strip()
        except NoSuchElementException:
            return ""
    
    def _extract_parameters(self, driver) -> Dict[str, Any]:
        """Extract property parameters (rooms, area, floor, etc.)"""
        params = {}
        
        try:
            # Look for parameters container
            params_container = driver.find_element(By.CSS_SELECTOR, self.selectors.AD_PARAMETERS)
            params_text = safe_extract_text(params_container)
            
            # Extract rooms
            rooms_match = re.search(r'(\d+)[\s-]*кімн', params_text, re.IGNORECASE)
            if rooms_match:
                params['rooms'] = int(rooms_match.group(1))
            
            # Extract area
            area_match = re.search(r'(\d+(?:[.,]\d+)?)\s*м²', params_text)
            if area_match:
                params['area'] = normalize_number(area_match.group(1))
            
            # Extract floor information
            floor_match = re.search(r'(\d+)\s*поверх', params_text, re.IGNORECASE)
            if floor_match:
                params['floor'] = int(floor_match.group(1))
            
            # Extract total floors
            floors_total_match = re.search(r'з\s*(\d+)', params_text, re.IGNORECASE)
            if floors_total_match:
                params['floors_total'] = int(floors_total_match.group(1))
            
            # Extract building type
            if 'новобудова' in params_text.lower():
                params['building_type'] = 'новобудова'
            elif 'цегла' in params_text.lower():
                params['building_type'] = 'цегла'
            elif 'панель' in params_text.lower():
                params['building_type'] = 'панель'
            
            # Extract renovation
            if 'євроремонт' in params_text.lower():
                params['renovation'] = 'євроремонт'
            elif 'косметичний' in params_text.lower():
                params['renovation'] = 'косметичний'
            elif 'під ремонт' in params_text.lower():
                params['renovation'] = 'під ремонт'
                
        except NoSuchElementException:
            logger.warning("Could not find parameters container")
        
        return params
    
    def _extract_seller_info(self, driver) -> Dict[str, Any]:
        """Extract seller information"""
        seller_data = {'type': 'unknown', 'name': None, 'signals': {}}
        
        try:
            # Try to get seller name
            try:
                seller_element = driver.find_element(By.CSS_SELECTOR, self.selectors.SELLER_NAME)
                seller_data['name'] = safe_extract_text(seller_element).strip()
            except NoSuchElementException:
                pass
            
            # Try to get seller type indicator
            try:
                type_element = driver.find_element(By.CSS_SELECTOR, self.selectors.SELLER_TYPE)
                type_text = safe_extract_text(type_element).lower()
                
                if 'приватна особа' in type_text:
                    seller_data['type'] = 'owner'
                    seller_data['signals']['type_indicator'] = 'приватна особа'
                else:
                    seller_data['type'] = 'agency'
                    seller_data['signals']['type_indicator'] = type_text
                    
            except NoSuchElementException:
                pass
                
        except Exception as e:
            logger.warning(f"Error extracting seller info: {str(e)}")
        
        return seller_data
    
    def _determine_district(self, location_text: str, description: str) -> Dict[str, Any]:
        """Determine district from location text and description"""
        district_info = {'district': None, 'street': None, 'source': 'unknown'}
        
        # Combine location and description for analysis
        combined_text = f"{location_text} {description}".lower()
        
        # Try street mapping first
        for street, district in self.street_mapping.items():
            if street.lower() in combined_text:
                district_info['district'] = district
                district_info['street'] = street
                district_info['source'] = 'street_mapping'
                return district_info
        
        # Try heuristic patterns
        district_patterns = {
            r'центр|галицьк|незалежност': 'Центр',
            r'пасічн|тролейбус': 'Пасічна',
            r'бам|івасюк|надрічн': 'БАМ',
            r'каскад|24\s*серпн': 'Каскад',
            r'вокзал|стефаник|залізнич': 'Залізничний (Вокзал)',
            r'брати|хо��кевич': 'Брати',
            r'софіїв|пстрак': 'Софіївка',
            r'будівельник|селянськ': 'Будівельників',
            r'набережн|дністров': 'Набережна',
            r'опришів|гуцульськ': 'Опришівці'
        }
        
        for pattern, district in district_patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                district_info['district'] = district
                district_info['source'] = 'text_heuristic'
                return district_info
        
        return district_info
