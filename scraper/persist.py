"""
Data persistence module
======================

Handles SQLite database operations and CSV exports with deduplication.
"""

import sqlite3
import pandas as pd
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .models import PropertyData
from .config import config

logger = logging.getLogger(__name__)

class DataPersistence:
    """Handles data storage, retrieval, and export operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.export_path = config.EXPORT_PATH
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS offers (
                    ad_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    price_value REAL,
                    price_currency TEXT DEFAULT 'USD',
                    location_city TEXT,
                    location_text TEXT,
                    district TEXT,
                    street TEXT,
                    rooms INTEGER,
                    area_total REAL,
                    floor INTEGER,
                    floors_total INTEGER,
                    building_type TEXT,
                    renovation TEXT,
                    description TEXT,
                    seller_type TEXT DEFAULT 'unknown',
                    seller_name TEXT,
                    seller_signals TEXT,
                    district_source TEXT DEFAULT 'unknown',
                    is_active BOOLEAN DEFAULT 1,
                    first_seen_at TEXT,
                    last_seen_at TEXT,
                    scraped_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indices for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON offers(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_district ON offers(district)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_price ON offers(price_value)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON offers(scraped_at)')
            
            # Create scraping sessions table for tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT,
                    end_time TEXT,
                    mode TEXT,
                    pages_scraped INTEGER,
                    total_processed INTEGER,
                    total_new INTEGER,
                    total_updated INTEGER,
                    total_errors INTEGER,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_property(self, property_data: PropertyData) -> Tuple[bool, str]:
        """
        Save or update property data in database
        
        Args:
            property_data: PropertyData object to save
            
        Returns:
            Tuple of (is_new, operation_type)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if property already exists
                existing = conn.execute(
                    'SELECT ad_id, first_seen_at FROM offers WHERE ad_id = ?',
                    (property_data.ad_id,)
                ).fetchone()
                
                if existing:
                    # Update existing property
                    property_data.first_seen_at = datetime.fromisoformat(existing[1])
                    property_data.last_seen_at = datetime.utcnow()
                    
                    conn.execute('''
                        UPDATE offers SET
                            title = ?, url = ?, price_value = ?, price_currency = ?,
                            location_city = ?, location_text = ?, district = ?, street = ?,
                            rooms = ?, area_total = ?, floor = ?, floors_total = ?,
                            building_type = ?, renovation = ?, description = ?,
                            seller_type = ?, seller_name = ?, seller_signals = ?,
                            district_source = ?, is_active = 1,
                            last_seen_at = ?, scraped_at = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE ad_id = ?
                    ''', (
                        property_data.title, property_data.url, property_data.price_value,
                        property_data.price_currency, property_data.location_city,
                        property_data.location_text, property_data.district, property_data.street,
                        property_data.rooms, property_data.area_total, property_data.floor,
                        property_data.floors_total, property_data.building_type,
                        property_data.renovation, property_data.description,
                        property_data.seller_type, property_data.seller_name,
                        json.dumps(property_data.seller_signals),
                        property_data.district_source,
                        property_data.last_seen_at.isoformat(),
                        property_data.scraped_at.isoformat(),
                        property_data.ad_id
                    ))
                    
                    conn.commit()
                    logger.debug(f"Updated property: {property_data.ad_id}")
                    return False, "updated"
                else:
                    # Insert new property
                    property_data.first_seen_at = datetime.utcnow()
                    property_data.last_seen_at = property_data.first_seen_at
                    
                    conn.execute('''
                        INSERT INTO offers (
                            ad_id, title, url, price_value, price_currency,
                            location_city, location_text, district, street,
                            rooms, area_total, floor, floors_total,
                            building_type, renovation, description,
                            seller_type, seller_name, seller_signals,
                            district_source, is_active,
                            first_seen_at, last_seen_at, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        property_data.ad_id, property_data.title, property_data.url,
                        property_data.price_value, property_data.price_currency,
                        property_data.location_city, property_data.location_text,
                        property_data.district, property_data.street,
                        property_data.rooms, property_data.area_total,
                        property_data.floor, property_data.floors_total,
                        property_data.building_type, property_data.renovation,
                        property_data.description, property_data.seller_type,
                        property_data.seller_name, json.dumps(property_data.seller_signals),
                        property_data.district_source, property_data.is_active,
                        property_data.first_seen_at.isoformat(),
                        property_data.last_seen_at.isoformat(),
                        property_data.scraped_at.isoformat()
                    ))
                    
                    conn.commit()
                    logger.debug(f"Inserted new property: {property_data.ad_id}")
                    return True, "inserted"
                    
        except Exception as e:
            logger.error(f"Error saving property {property_data.ad_id}: {str(e)}")
            return False, "error"
    
    def save_properties_batch(self, properties: List[PropertyData]) -> Dict[str, int]:
        """
        Save multiple properties in a batch
        
        Args:
            properties: List of PropertyData objects
            
        Returns:
            Dictionary with counts of operations
        """
        results = {"new": 0, "updated": 0, "errors": 0}
        
        for prop in properties:
            try:
                is_new, operation = self.save_property(prop)
                if operation == "inserted":
                    results["new"] += 1
                elif operation == "updated":
                    results["updated"] += 1
                elif operation == "error":
                    results["errors"] += 1
            except Exception as e:
                logger.error(f"Error in batch save for {prop.ad_id}: {str(e)}")
                results["errors"] += 1
        
        logger.info(f"Batch save completed: {results}")
        return results
    
    def mark_inactive_properties(self, seen_ad_ids: List[str], session_time: datetime):
        """
        Mark properties as inactive if they weren't seen in current session
        
        Args:
            seen_ad_ids: List of ad_ids that were seen in current session
            session_time: Time of current scraping session
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if seen_ad_ids:
                    # Convert list to comma-separated string for SQL
                    placeholders = ','.join(['?' for _ in seen_ad_ids])
                    
                    conn.execute(f'''
                        UPDATE offers 
                        SET is_active = 0, last_seen_at = ?
                        WHERE ad_id NOT IN ({placeholders}) AND is_active = 1
                    ''', [session_time.isoformat()] + seen_ad_ids)
                else:
                    # No properties seen - mark all as inactive
                    conn.execute('''
                        UPDATE offers 
                        SET is_active = 0, last_seen_at = ?
                        WHERE is_active = 1
                    ''', (session_time.isoformat(),))
                
                affected = conn.total_changes
                conn.commit()
                logger.info(f"Marked {affected} properties as inactive")
                
        except Exception as e:
            logger.error(f"Error marking inactive properties: {str(e)}")
    
    def get_active_properties(self) -> List[Dict[str, Any]]:
        """Get all active properties from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM offers 
                    WHERE is_active = 1 
                    ORDER BY scraped_at DESC
                ''')
                
                properties = []
                for row in cursor.fetchall():
                    prop_dict = dict(row)
                    # Parse seller_signals JSON
                    if prop_dict.get('seller_signals'):
                        try:
                            prop_dict['seller_signals'] = json.loads(prop_dict['seller_signals'])
                        except json.JSONDecodeError:
                            prop_dict['seller_signals'] = {}
                    
                    properties.append(prop_dict)
                
                logger.info(f"Retrieved {len(properties)} active properties")
                return properties
                
        except Exception as e:
            logger.error(f"Error retrieving active properties: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Total counts
                cursor = conn.execute('SELECT COUNT(*) FROM offers')
                stats['total_properties'] = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(*) FROM offers WHERE is_active = 1')
                stats['active_properties'] = cursor.fetchone()[0]
                
                # By seller type
                cursor = conn.execute('''
                    SELECT seller_type, COUNT(*) 
                    FROM offers WHERE is_active = 1 
                    GROUP BY seller_type
                ''')
                stats['by_seller_type'] = dict(cursor.fetchall())
                
                # By district
                cursor = conn.execute('''
                    SELECT district, COUNT(*) 
                    FROM offers WHERE is_active = 1 AND district IS NOT NULL
                    GROUP BY district 
                    ORDER BY COUNT(*) DESC
                ''')
                stats['by_district'] = dict(cursor.fetchall())
                
                # Price statistics
                cursor = conn.execute('''
                    SELECT 
                        AVG(price_value) as avg_price,
                        MIN(price_value) as min_price,
                        MAX(price_value) as max_price,
                        COUNT(price_value) as priced_properties
                    FROM offers 
                    WHERE is_active = 1 AND price_value IS NOT NULL
                ''')
                price_stats = cursor.fetchone()
                stats['price_stats'] = {
                    'avg_price': round(price_stats[0], 2) if price_stats[0] else 0,
                    'min_price': price_stats[1] or 0,
                    'max_price': price_stats[2] or 0,
                    'priced_properties': price_stats[3] or 0
                }
                
                # Last update
                cursor = conn.execute('''
                    SELECT MAX(scraped_at) FROM offers WHERE is_active = 1
                ''')
                last_update = cursor.fetchone()[0]
                stats['last_update'] = last_update
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def export_to_csv(self, filepath: str = None) -> bool:
        """
        Export active properties to CSV
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            True if export successful
        """
        export_path = filepath or self.export_path
        
        try:
            # Ensure export directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            properties = self.get_active_properties()
            
            if not properties:
                logger.warning("No active properties to export")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(properties)
            
            # Clean up seller_signals for CSV (convert back to JSON string)
            if 'seller_signals' in df.columns:
                df['seller_signals'] = df['seller_signals'].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )
            
            # Export to CSV
            df.to_csv(export_path, index=False, encoding='utf-8')
            logger.info(f"Exported {len(properties)} properties to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def save_scraping_session(self, session_data: Dict[str, Any]) -> bool:
        """Save scraping session information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO scraping_sessions (
                        session_id, start_time, end_time, mode,
                        pages_scraped, total_processed, total_new, total_updated,
                        total_errors, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_data['session_id'],
                    session_data['start_time'],
                    session_data['end_time'],
                    session_data['mode'],
                    session_data['pages_scraped'],
                    session_data['total_processed'],
                    session_data['total_new'],
                    session_data['total_updated'],
                    session_data['total_errors'],
                    session_data['success'],
                    session_data.get('error_message')
                ))
                
                conn.commit()
                logger.info(f"Saved scraping session: {session_data['session_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving scraping session: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Remove old scraping session records"""
        try:
            cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - \
                         datetime.timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM scraping_sessions 
                    WHERE start_time < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted} old scraping sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {str(e)}")
