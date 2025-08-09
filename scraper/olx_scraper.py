"""
Botasaurus OLX Scraper - Module 1
Anti-detection web scraping for Ivano-Frankivsk real estate listings
"""

import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import json
import re

from botasaurus import *
from botasaurus.request import Request, Response
from botasaurus.browser import Browser
from bs4 import BeautifulSoup
import pandas as pd

from .config import ScrapingConfig, STREET_TO_DISTRICT, OWNER_KEYWORDS, AGENCY_KEYWORDS
from .persist import DatabaseManager
from .classify import classify_seller
from .utils import Logger, extract_price, extract_area, clean_text


@dataclass
class Property:
    """Property listing data structure"""
    olx_id: str
    title: str
    price_usd: Optional[float]
    currency: str
    area: Optional[float]
    floor: Optional[int]
    total_floors: Optional[int]
    rooms: Optional[int]
    district: str
    street: Optional[str]
    full_location: str
    description: str
    seller_type: str  # 'owner' or 'agency'
    listing_type: str  # 'rent' or 'sale'
    listing_url: str
    image_url: Optional[str]
    posted_date: Optional[str]
    is_promoted: bool
    scraped_at: datetime
    building_type: Optional[str]
    renovation_status: Optional[str]


class BotasaurusOLXScraper:
    """
    Anti-detection OLX scraper using Botasaurus framework
    Features: stealth mode, user-agent rotation, random delays, resume capability
    """
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.logger = Logger(self.config.LOG_FILE, self.config.LOG_LEVEL)
        self.db_manager = DatabaseManager(self.config.DB_URL)
        self.properties: List[Property] = []
        self.stats = {
            'total_processed': 0,
            'new_listings': 0,
            'updated_listings': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    @browser(
        stealth=True,
        headless=True,
        user_agent=AntiDetectionUserAgent(),
        block_resources=True,
        wait_for_complete_page_load=True
    )
    def scrape_olx_listings(self, driver: AntiDetectionDriver, data):
        """
        Main scraping method with Botasaurus anti-detection
        """
        self.stats['start_time'] = datetime.now()
        self.logger.info("🚀 Starting Botasaurus OLX scraper for Ivano-Frankivsk")
        
        try:
            listing_type = data.get('listing_type', 'sale')
            max_pages = data.get('max_pages', self.config.MAX_PAGES)
            
            base_url = self._get_search_url(listing_type)
            
            for page in range(1, max_pages + 1):
                url = f"{base_url}&page={page}"
                self.logger.info(f"📄 Scraping page {page}/{max_pages}: {url}")
                
                try:
                    # Navigate with random delay
                    self._random_delay()
                    driver.get(url)
                    
                    # Wait for listings to load
                    driver.wait_for_element(self.config.SELECTORS['listing_container'], timeout=10)
                    
                    # Parse listings on current page
                    page_properties = self._parse_page(driver, listing_type)
                    self.properties.extend(page_properties)
                    
                    self.logger.info(f"✅ Page {page}: Found {len(page_properties)} listings")
                    
                    # Check if last page (no more listings)
                    if len(page_properties) == 0:
                        self.logger.info(f"📭 No more listings found on page {page}, stopping")
                        break
                        
                except Exception as e:
                    self.logger.error(f"❌ Error scraping page {page}: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            # Save results
            self._save_results()
            self.stats['end_time'] = datetime.now()
            
            self.logger.info(f"🎉 Scraping completed! Stats: {self.stats}")
            return self.stats
            
        except Exception as e:
            self.logger.error(f"💥 Critical error in scraper: {str(e)}")
            raise
    
    def _get_search_url(self, listing_type: str) -> str:
        """Generate search URL based on listing type"""
        base_url = self.config.CITY_URL
        
        if listing_type == "rent":
            base_url += "arenda/"
        elif listing_type == "sale": 
            base_url += "prodazha/"
            
        # Add USD currency filter
        base_url += "?currency=USD"
        
        return base_url
    
    def _parse_page(self, driver: AntiDetectionDriver, listing_type: str) -> List[Property]:
        """Parse all listings on current page"""
        properties = []
        
        try:
            # Get page HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all listing containers
            listing_containers = soup.select(self.config.SELECTORS['listing_container'])
            self.logger.info(f"🔍 Found {len(listing_containers)} listing containers")
            
            for container in listing_containers:
                try:
                    property_data = self._parse_single_listing(container, listing_type)
                    if property_data:
                        properties.append(property_data)
                        self.stats['total_processed'] += 1
                except Exception as e:
                    self.logger.error(f"❌ Error parsing listing: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ Error parsing page: {str(e)}")
            
        return properties
    
    def _parse_single_listing(self, container, listing_type: str) -> Optional[Property]:
        """Parse single property listing"""
        try:
            # Extract basic info
            title_elem = container.select_one(self.config.SELECTORS['title'])
            price_elem = container.select_one(self.config.SELECTORS['price'])
            location_elem = container.select_one(self.config.SELECTORS['location'])
            link_elem = container.select_one(self.config.SELECTORS['link'])
            
            if not all([title_elem, price_elem, location_elem, link_elem]):
                return None
            
            # Extract data
            title = clean_text(title_elem.get_text())
            price_text = clean_text(price_elem.get_text())
            location_text = clean_text(location_elem.get_text())
            listing_url = link_elem.get('href', '')
            
            # Ensure full URL
            if listing_url.startswith('/'):
                listing_url = self.config.BASE_URL + listing_url
            
            # Extract OLX ID from URL
            olx_id = self._extract_olx_id(listing_url)
            if not olx_id:
                return None
            
            # Parse price
            price_usd, currency = extract_price(price_text)
            if currency != "USD":
                return None  # Skip non-USD listings
                
            # Parse area and other details
            area = extract_area(title)
            
            # Determine district and street
            district, street = self._determine_location(location_text)
            
            # Extract additional details
            details = self._extract_details(container)
            
            # Classify seller
            seller_type = classify_seller(title, details.get('description', ''))
            
            # Check for promoted listing
            is_promoted = container.select_one(self.config.SELECTORS['promoted']) is not None
            
            # Get image URL
            image_elem = container.select_one(self.config.SELECTORS['image'])
            image_url = image_elem.get('src') if image_elem else None
            
            # Create property object
            property_obj = Property(
                olx_id=olx_id,
                title=title,
                price_usd=price_usd,
                currency=currency,
                area=area,
                floor=details.get('floor'),
                total_floors=details.get('total_floors'),
                rooms=details.get('rooms'),
                district=district,
                street=street,
                full_location=location_text,
                description=details.get('description', ''),
                seller_type=seller_type,
                listing_type=listing_type,
                listing_url=listing_url,
                image_url=image_url,
                posted_date=details.get('posted_date'),
                is_promoted=is_promoted,
                scraped_at=datetime.now(),
                building_type=details.get('building_type'),
                renovation_status=details.get('renovation_status')
            )
            
            self.logger.debug(f"✅ Parsed: {title[:50]}... | {price_usd} USD | {district}")
            return property_obj
            
        except Exception as e:
            self.logger.error(f"❌ Error parsing single listing: {str(e)}")
            return None
    
    def _extract_olx_id(self, url: str) -> Optional[str]:
        """Extract OLX ID from listing URL"""
        try:
            # OLX URLs typically contain ID like: .../ID-item.html
            match = re.search(r'/(\d+)-', url)
            if match:
                return match.group(1)
            
            # Alternative pattern
            match = re.search(r'ID(\d+)', url)
            if match:
                return match.group(1)
                
            return None
        except:
            return None
    
    def _determine_location(self, location_text: str) -> tuple[str, Optional[str]]:
        """Determine district and street from location text"""
        location_lower = location_text.lower()
        
        # Try to find street in mapping
        for street, district in STREET_TO_DISTRICT.items():
            if street.lower() in location_lower:
                return district, street
        
        # Try to find district directly
        for district in self.config.DISTRICTS:
            if district.lower() in location_lower:
                return district, None
        
        # Default district
        return self.config.DEFAULT_DISTRICT, None
    
    def _extract_details(self, container) -> Dict[str, Any]:
        """Extract additional details from listing container"""
        details = {}
        
        try:
            # Look for details section
            details_elem = container.select_one(self.config.SELECTORS['details'])
            if details_elem:
                details_text = clean_text(details_elem.get_text())
                
                # Extract rooms
                rooms_match = re.search(r'(\d+)\s*кімн', details_text, re.IGNORECASE)
                if rooms_match:
                    details['rooms'] = int(rooms_match.group(1))
                
                # Extract floor
                floor_match = re.search(r'(\d+)\s*/\s*(\d+)\s*поверх', details_text, re.IGNORECASE)
                if floor_match:
                    details['floor'] = int(floor_match.group(1))
                    details['total_floors'] = int(floor_match.group(2))
            
            # Look for date
            date_elem = container.select_one(self.config.SELECTORS['date'])
            if date_elem:
                details['posted_date'] = clean_text(date_elem.get_text())
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting details: {str(e)}")
        
        return details
    
    def _random_delay(self):
        """Random delay to avoid detection"""
        delay = random.randint(self.config.MIN_DELAY, self.config.MAX_DELAY) / 1000
        time.sleep(delay)
    
    def _save_results(self):
        """Save scraped properties to database and CSV"""
        if not self.properties:
            self.logger.warning("⚠️ No properties to save")
            return
        
        try:
            # Save to database
            new_count, updated_count = self.db_manager.save_properties(self.properties)
            self.stats['new_listings'] = new_count
            self.stats['updated_listings'] = updated_count
            
            # Export to CSV
            if self.config.EXPORT_CSV:
                self._export_to_csv()
            
            self.logger.info(f"💾 Saved: {new_count} new, {updated_count} updated listings")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {str(e)}")
    
    def _export_to_csv(self):
        """Export properties to CSV file"""
        try:
            df = pd.DataFrame([asdict(prop) for prop in self.properties])
            df.to_csv(self.config.CSV_PATH, index=False, encoding='utf-8')
            self.logger.info(f"📊 Exported {len(df)} listings to {self.config.CSV_PATH}")
        except Exception as e:
            self.logger.error(f"❌ Error exporting CSV: {str(e)}")


def run_scraper(listing_type: str = "sale", max_pages: int = 10) -> Dict[str, Any]:
    """
    Main entry point for running the scraper
    """
    config = ScrapingConfig()
    scraper = BotasaurusOLXScraper(config)
    
    data = {
        'listing_type': listing_type,
        'max_pages': max_pages
    }
    
    return scraper.scrape_olx_listings(data)


if __name__ == "__main__":
    # Run scraper standalone
    stats = run_scraper(listing_type="sale", max_pages=5)
    print(f"Scraping completed: {stats}")
