"""
Utilities for CLI and API server
Logging, event management, and helper functions
"""

import logging
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any


class Logger:
    """Custom logger for CLI operations"""
    
    def __init__(self, log_file: str, level: str = "INFO"):
        self.logger = logging.getLogger("property_monitor_api")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create log directory if not exists
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


class EventLogger:
    """Event logger for system activities"""
    
    def __init__(self, db_path: str = None):
        from .db_config import get_db_path
        self.db_path = db_path if db_path else get_db_path()
        self.logger = Logger("cli/logs/events.log")
        
    def log_event(self, module: str, action: str, details: str, status: str = "INFO"):
        """Log system event to database"""
        try:
            if not os.path.exists(self.db_path):
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO event_log (module, action, details, status)
                VALUES (?, ?, ?, ?)
            """, (module, action, details, status))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error logging event: {str(e)}")
    
    def get_recent_events(self, since_id: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events from database"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM event_log 
                WHERE id > ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (since_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting recent events: {str(e)}")
            return []


def ensure_database_schema(db_path: str = None):
    """Ensure database has all required tables"""
    from .db_config import get_db_path
    if not db_path:
        db_path = get_db_path()
    try:
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Properties table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                olx_id TEXT UNIQUE,
                title TEXT,
                price_usd REAL,
                currency TEXT DEFAULT 'USD',
                area REAL,
                floor INTEGER,
                total_floors INTEGER,
                rooms INTEGER,
                district TEXT,
                street TEXT,
                full_location TEXT,
                description TEXT,
                seller_type TEXT,
                listing_type TEXT,
                listing_url TEXT,
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
        
        # Street to district mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS street_district_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street TEXT UNIQUE,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Event log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                module TEXT,
                action TEXT,
                details TEXT,
                status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error ensuring database schema: {e}")
        return False
