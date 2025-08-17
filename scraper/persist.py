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
        else:
            # Use unified DB path from config
            from cli.db_config import get_db_path
            self.db_path = get_db_path()
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
            # Log database path for consistency verification
            import os
            abs_db_path = os.path.abspath(self.db_path)
            self.logger.info(f"📊 Python Scraper DB path: {abs_db_path}")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Properties table - COMPATIBLE WITH NODE.JS SCHEMA
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        olx_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        price_usd INTEGER NOT NULL,
                        area INTEGER NOT NULL,
                        rooms INTEGER,
                        floor INTEGER,
                        street TEXT,
                        district TEXT NOT NULL,
                        description TEXT,
                        is_owner BOOLEAN NOT NULL DEFAULT 0,
                        url TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Street to district mapping table - COMPATIBLE WITH NODE.JS
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS street_districts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        street TEXT UNIQUE NOT NULL,
                        district TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Activity log table - COMPATIBLE WITH NODE.JS
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        type TEXT DEFAULT 'info'
                    )
                """)
                
                # Price history table - COMPATIBLE WITH NODE.JS
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        property_id INTEGER NOT NULL,
                        olx_id TEXT NOT NULL,
                        price_usd INTEGER NOT NULL,
                        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (property_id) REFERENCES properties (id)
                    )
                """)

                # Scraping state table - COMPATIBLE WITH NODE.JS
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_state (
                        id INTEGER PRIMARY KEY,
                        last_page INTEGER DEFAULT 0,
                        last_url TEXT,
                        last_processed_id TEXT,
                        total_processed INTEGER DEFAULT 0,
                        last_run DATETIME,
                        status TEXT DEFAULT 'idle'
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_olx_id ON properties(olx_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_district ON properties(district)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at)")
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
        """Insert new property into database - Node.js compatible schema"""
        insert_sql = """
            INSERT INTO properties (
                olx_id, title, price_usd, area, rooms, floor, street, district,
                description, is_owner, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Convert seller_type to is_owner boolean for compatibility
        is_owner = 1 if prop_dict.get('seller_type') == 'owner' else 0

        # Convert price and area to integers (Node.js schema)
        price_usd = int(prop_dict.get('price_usd', 0)) if prop_dict.get('price_usd') else 0
        area = int(prop_dict.get('area', 0)) if prop_dict.get('area') else 0

        values = (
            prop_dict['olx_id'],
            prop_dict['title'],
            price_usd,
            area,
            prop_dict.get('rooms'),
            prop_dict.get('floor'),
            prop_dict.get('street'),
            prop_dict['district'],
            prop_dict.get('description', ''),
            is_owner,
            prop_dict.get('listing_url', '')
            prop_dict.get('is_promoted', False),
        )

        cursor.execute(insert_sql, values)

        # Also add to price history if price exists
        if price_usd > 0:
            property_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO price_history (property_id, olx_id, price_usd)
                VALUES (?, ?, ?)
            """, (property_id, prop_dict['olx_id'], price_usd))
    
    def _update_property(self, cursor, prop_dict: Dict[str, Any], property_id: int):
        """Update existing property in database - Node.js compatible schema"""
        update_sql = """
            UPDATE properties SET
                title = ?, price_usd = ?, area = ?, rooms = ?, floor = ?,
                street = ?, district = ?, description = ?, is_owner = ?,
                url = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        # Convert seller_type to is_owner boolean for compatibility
        is_owner = 1 if prop_dict.get('seller_type') == 'owner' else 0

        # Convert price and area to integers (Node.js schema)
        price_usd = int(prop_dict.get('price_usd', 0)) if prop_dict.get('price_usd') else 0
        area = int(prop_dict.get('area', 0)) if prop_dict.get('area') else 0

        values = (
            prop_dict['title'],
            price_usd,
            area,
            prop_dict.get('rooms'),
            prop_dict.get('floor'),
            prop_dict.get('street'),
            prop_dict['district'],
            prop_dict.get('description', ''),
            is_owner,
            prop_dict.get('listing_url', ''),
            property_id
        )

        cursor.execute(update_sql, values)

        # Add price change to history if different
        if price_usd > 0:
            cursor.execute("""
                SELECT price_usd FROM price_history
                WHERE olx_id = ? ORDER BY recorded_at DESC LIMIT 1
            """, (prop_dict['olx_id'],))
            last_price = cursor.fetchone()

            if not last_price or last_price[0] != price_usd:
                cursor.execute("""
                    INSERT INTO price_history (property_id, olx_id, price_usd)
                    VALUES (?, ?, ?)
                """, (property_id, prop_dict['olx_id'], price_usd))
    
    def _log_event(self, cursor, module: str, action: str, details: str = "",
                   status: str = "INFO", properties_count: int = 0):
        """Log event to activity_log table - Node.js compatible"""
        message = f"{module.upper()}: {action} - {details}"
        if properties_count > 0:
            message += f" (properties: {properties_count})"

        cursor.execute("""
            INSERT INTO activity_log (message, type)
            VALUES (?, ?)
        """, (message, status.lower()))
    
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
