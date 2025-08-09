"""
Database persistence module for scraped properties
Handles SQLite/PostgreSQL storage with deduplication
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
import json
from dataclasses import asdict

from .utils import Logger


class DatabaseManager:
    """
    Database manager for property listings with deduplication
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.logger = Logger("scraper/logs/database.log")
        
        # Extract database path from URL
        if db_url.startswith("sqlite:///"):
            self.db_path = db_url.replace("sqlite:///", "")
            self._ensure_directories()
            self._init_sqlite_db()
        else:
            raise ValueError("Only SQLite databases are supported currently")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs("scraper/logs", exist_ok=True)
    
    def _init_sqlite_db(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Properties table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        olx_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        price_usd REAL,
                        currency TEXT DEFAULT 'USD',
                        area REAL,
                        floor INTEGER,
                        total_floors INTEGER,
                        rooms INTEGER,
                        district TEXT NOT NULL,
                        street TEXT,
                        full_location TEXT,
                        description TEXT,
                        seller_type TEXT CHECK(seller_type IN ('owner', 'agency')),
                        listing_type TEXT CHECK(listing_type IN ('rent', 'sale')),
                        listing_url TEXT NOT NULL,
                        image_url TEXT,
                        posted_date TEXT,
                        is_promoted BOOLEAN DEFAULT FALSE,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        building_type TEXT,
                        renovation_status TEXT,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Street to district mapping table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS street_district_map (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        street TEXT UNIQUE NOT NULL,
                        district TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Event log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS event_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        module TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        status TEXT CHECK(status IN ('INFO', 'WARNING', 'ERROR', 'SUCCESS')),
                        properties_count INTEGER DEFAULT 0
                    )
                """)
                
                # Scraping sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        listing_type TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        total_pages INTEGER DEFAULT 0,
                        total_processed INTEGER DEFAULT 0,
                        new_listings INTEGER DEFAULT 0,
                        updated_listings INTEGER DEFAULT 0,
                        errors INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'running'
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_olx_id ON properties(olx_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_district ON properties(district)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_scraped_at ON properties(scraped_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price_usd)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_active ON properties(is_active)")
                
                conn.commit()
                self.logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing database: {str(e)}")
            raise
    
    def save_properties(self, properties: List) -> Tuple[int, int]:
        """
        Save properties to database with deduplication
        
        Args:
            properties: List of Property objects
            
        Returns:
            Tuple[int, int]: (new_count, updated_count)
        """
        if not properties:
            return 0, 0
        
        new_count = 0
        updated_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for property_obj in properties:
                    try:
                        # Convert property object to dict
                        if hasattr(property_obj, '__dict__'):
                            prop_dict = asdict(property_obj)
                        else:
                            prop_dict = property_obj
                        
                        # Check if property already exists
                        cursor.execute(
                            "SELECT id, updated_at FROM properties WHERE olx_id = ?",
                            (prop_dict['olx_id'],)
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update existing property
                            self._update_property(cursor, prop_dict, existing[0])
                            updated_count += 1
                        else:
                            # Insert new property
                            self._insert_property(cursor, prop_dict)
                            new_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ Error saving property {prop_dict.get('olx_id', 'unknown')}: {str(e)}")
                        continue
                
                conn.commit()
                
                # Log the operation
                self._log_event(
                    cursor,
                    module="scraper",
                    action="save_properties",
                    details=f"Saved {new_count} new, updated {updated_count} existing properties",
                    status="SUCCESS",
                    properties_count=len(properties)
                )
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Error in save_properties: {str(e)}")
            raise
        
        return new_count, updated_count
    
    def _insert_property(self, cursor, prop_dict: Dict[str, Any]):
        """Insert new property into database"""
        insert_sql = """
            INSERT INTO properties (
                olx_id, title, price_usd, currency, area, floor, total_floors,
                rooms, district, street, full_location, description, seller_type,
                listing_type, listing_url, image_url, posted_date, is_promoted,
                scraped_at, building_type, renovation_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            prop_dict['olx_id'],
            prop_dict['title'],
            prop_dict.get('price_usd'),
            prop_dict.get('currency', 'USD'),
            prop_dict.get('area'),
            prop_dict.get('floor'),
            prop_dict.get('total_floors'),
            prop_dict.get('rooms'),
            prop_dict['district'],
            prop_dict.get('street'),
            prop_dict.get('full_location'),
            prop_dict.get('description', ''),
            prop_dict.get('seller_type', 'agency'),
            prop_dict.get('listing_type', 'sale'),
            prop_dict['listing_url'],
            prop_dict.get('image_url'),
            prop_dict.get('posted_date'),
            prop_dict.get('is_promoted', False),
            prop_dict.get('scraped_at', datetime.now()),
            prop_dict.get('building_type'),
            prop_dict.get('renovation_status')
        )
        
        cursor.execute(insert_sql, values)
    
    def _update_property(self, cursor, prop_dict: Dict[str, Any], property_id: int):
        """Update existing property in database"""
        update_sql = """
            UPDATE properties SET
                title = ?, price_usd = ?, currency = ?, area = ?, floor = ?,
                total_floors = ?, rooms = ?, district = ?, street = ?,
                full_location = ?, description = ?, seller_type = ?,
                listing_type = ?, listing_url = ?, image_url = ?, posted_date = ?,
                is_promoted = ?, updated_at = ?, building_type = ?, renovation_status = ?
            WHERE id = ?
        """
        
        values = (
            prop_dict['title'],
            prop_dict.get('price_usd'),
            prop_dict.get('currency', 'USD'),
            prop_dict.get('area'),
            prop_dict.get('floor'),
            prop_dict.get('total_floors'),
            prop_dict.get('rooms'),
            prop_dict['district'],
            prop_dict.get('street'),
            prop_dict.get('full_location'),
            prop_dict.get('description', ''),
            prop_dict.get('seller_type', 'agency'),
            prop_dict.get('listing_type', 'sale'),
            prop_dict['listing_url'],
            prop_dict.get('image_url'),
            prop_dict.get('posted_date'),
            prop_dict.get('is_promoted', False),
            datetime.now(),
            prop_dict.get('building_type'),
            prop_dict.get('renovation_status'),
            property_id
        )
        
        cursor.execute(update_sql, values)
    
    def _log_event(self, cursor, module: str, action: str, details: str = "", 
                   status: str = "INFO", properties_count: int = 0):
        """Log event to event_log table"""
        cursor.execute("""
            INSERT INTO event_log (module, action, details, status, properties_count)
            VALUES (?, ?, ?, ?, ?)
        """, (module, action, details, status, properties_count))
    
    def get_properties(self, limit: int = 100, district: str = None, 
                      listing_type: str = None) -> List[Dict[str, Any]]:
        """
        Get properties from database with filters
        
        Args:
            limit: Maximum number of properties to return
            district: Filter by district
            listing_type: Filter by listing type ('rent' or 'sale')
            
        Returns:
            List[Dict[str, Any]]: List of properties
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.cursor()
                
                sql = "SELECT * FROM properties WHERE is_active = 1"
                params = []
                
                if district:
                    sql += " AND district = ?"
                    params.append(district)
                
                if listing_type:
                    sql += " AND listing_type = ?"
                    params.append(listing_type)
                
                sql += " ORDER BY scraped_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting properties: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total properties
                cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
                total_properties = cursor.fetchone()[0]
                
                # By seller type
                cursor.execute("""
                    SELECT seller_type, COUNT(*) 
                    FROM properties 
                    WHERE is_active = 1 
                    GROUP BY seller_type
                """)
                seller_stats = dict(cursor.fetchall())
                
                # By district
                cursor.execute("""
                    SELECT district, COUNT(*) 
                    FROM properties 
                    WHERE is_active = 1 
                    GROUP BY district 
                    ORDER BY COUNT(*) DESC
                """)
                district_stats = dict(cursor.fetchall())
                
                # Average price by district
                cursor.execute("""
                    SELECT district, AVG(price_usd) 
                    FROM properties 
                    WHERE is_active = 1 AND price_usd IS NOT NULL 
                    GROUP BY district
                """)
                avg_prices = dict(cursor.fetchall())
                
                # Latest scraping session
                cursor.execute("""
                    SELECT * FROM scraping_sessions 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """)
                latest_session = cursor.fetchone()
                
                return {
                    'total_properties': total_properties,
                    'seller_stats': seller_stats,
                    'district_stats': district_stats,
                    'avg_prices': avg_prices,
                    'latest_session': dict(latest_session) if latest_session else None
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting statistics: {str(e)}")
            return {}
    
    def save_street_mapping(self, street: str, district: str) -> bool:
        """Save street to district mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO street_district_map (street, district)
                    VALUES (?, ?)
                """, (street, district))
                
                conn.commit()
                self.logger.info(f"✅ Saved street mapping: {street} -> {district}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error saving street mapping: {str(e)}")
            return False
    
    def get_street_mappings(self) -> Dict[str, str]:
        """Get all street to district mappings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT street, district FROM street_district_map")
                rows = cursor.fetchall()
                
                return dict(rows)
                
        except Exception as e:
            self.logger.error(f"❌ Error getting street mappings: {str(e)}")
            return {}
