"""
Data models for OLX property information
=======================================

Defines the structure for property data and related models.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

@dataclass
class PropertyData:
    """Data model for a property listing from OLX"""
    
    # Required fields
    ad_id: str
    title: str
    url: str
    price_value: Optional[float]
    price_currency: str
    location_city: str
    location_text: str
    
    # Property details
    district: Optional[str] = None
    street: Optional[str] = None
    rooms: Optional[int] = None
    area_total: Optional[float] = None
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    building_type: Optional[str] = None
    renovation: Optional[str] = None
    
    # Content
    description: str = ""
    
    # Seller information
    seller_type: str = "unknown"  # owner/agency/unknown
    seller_name: Optional[str] = None
    seller_signals: Dict[str, Any] = None
    
    # Metadata
    district_source: str = "unknown"  # street_mapping/text_heuristic/unknown
    is_active: bool = True
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values and validate data"""
        if self.seller_signals is None:
            self.seller_signals = {}
        
        # Set timestamps if not provided
        now = datetime.utcnow()
        if self.scraped_at is None:
            self.scraped_at = now
        if self.first_seen_at is None:
            self.first_seen_at = now
        if self.last_seen_at is None:
            self.last_seen_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'ad_id': self.ad_id,
            'title': self.title,
            'url': self.url,
            'price_value': self.price_value,
            'price_currency': self.price_currency,
            'location_city': self.location_city,
            'location_text': self.location_text,
            'district': self.district,
            'street': self.street,
            'rooms': self.rooms,
            'area_total': self.area_total,
            'floor': self.floor,
            'floors_total': self.floors_total,
            'building_type': self.building_type,
            'renovation': self.renovation,
            'description': self.description,
            'seller_type': self.seller_type,
            'seller_name': self.seller_name,
            'seller_signals': json.dumps(self.seller_signals) if self.seller_signals else None,
            'district_source': self.district_source,
            'is_active': self.is_active,
            'first_seen_at': self.first_seen_at.isoformat() if self.first_seen_at else None,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyData':
        """Create instance from dictionary"""
        # Parse timestamps
        for field in ['first_seen_at', 'last_seen_at', 'scraped_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Parse seller signals
        if data.get('seller_signals'):
            data['seller_signals'] = json.loads(data['seller_signals'])
        
        return cls(**data)

@dataclass 
class ScrapingResult:
    """Result of a scraping session"""
    
    success: bool
    total_processed: int
    total_new: int
    total_updated: int
    total_errors: int
    pages_scraped: int
    start_time: datetime
    end_time: datetime
    error_message: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate scraping duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'success': self.success,
            'total_processed': self.total_processed,
            'total_new': self.total_new,
            'total_updated': self.total_updated,
            'total_errors': self.total_errors,
            'pages_scraped': self.pages_scraped,
            'duration_seconds': self.duration_seconds,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'error_message': self.error_message
        }

@dataclass
class SellerClassificationResult:
    """Result of seller type classification"""
    
    seller_type: str  # owner/agency
    confidence: float  # 0.0 to 1.0
    signals: Dict[str, Any]  # What triggered this classification
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'seller_type': self.seller_type,
            'confidence': self.confidence,
            'signals': self.signals
        }
