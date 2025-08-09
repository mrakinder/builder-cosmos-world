"""
Feature Engineering Module for Property Price Prediction
Creates optimized features for LightAutoML training
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer


class FeatureEngineer:
    """
    Feature engineering for property price prediction
    """
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set for price prediction
        
        Args:
            df: Raw property data
            
        Returns:
            pd.DataFrame: Engineered features
        """
        # Make a copy to avoid modifying original
        features_df = df.copy()
        
        # 1. Basic numeric features
        features_df = self._create_basic_features(features_df)
        
        # 2. Location-based features
        features_df = self._create_location_features(features_df)
        
        # 3. Property characteristics features
        features_df = self._create_property_features(features_df)
        
        # 4. Text-based features
        features_df = self._create_text_features(features_df)
        
        # 5. Temporal features
        features_df = self._create_temporal_features(features_df)
        
        # 6. Market-based features
        features_df = self._create_market_features(features_df)
        
        # 7. Clean and prepare final feature set
        features_df = self._clean_features(features_df)
        
        return features_df
    
    def _create_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create basic numeric features"""
        
        # Area-related features
        df['area_log'] = np.log1p(df['area'].fillna(0))
        df['area_sqrt'] = np.sqrt(df['area'].fillna(0))
        df['area_per_room'] = df['area'] / df['rooms'].replace(0, 1).fillna(1)
        
        # Price-related features (target is price_usd)
        df['price_per_sqm'] = df['price_usd'] / df['area'].replace(0, np.nan)
        
        # Floor-related features
        df['floor_ratio'] = df['floor'] / df['total_floors'].replace(0, np.nan)
        df['is_ground_floor'] = (df['floor'] == 1).astype(int)
        df['is_top_floor'] = (df['floor'] == df['total_floors']).astype(int)
        df['is_middle_floor'] = ((df['floor'] > 1) & (df['floor'] < df['total_floors'])).astype(int)
        
        # Room-related features
        df['rooms_filled'] = df['rooms'].fillna(df['rooms'].median())
        df['is_studio'] = (df['rooms_filled'] <= 1).astype(int)
        df['is_large_apartment'] = (df['rooms_filled'] >= 4).astype(int)
        
        return df
    
    def _create_location_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create location-based features"""
        
        # District encoding
        df['district_filled'] = df['district'].fillna('Центр')
        
        # Create district dummies
        district_dummies = pd.get_dummies(df['district_filled'], prefix='district')
        df = pd.concat([df, district_dummies], axis=1)
        
        # District ranking by average price (if available)
        if 'price_usd' in df.columns:
            district_price_rank = df.groupby('district_filled')['price_usd'].median().rank()
            df['district_price_rank'] = df['district_filled'].map(district_price_rank)
        
        # Street availability
        df['has_street_info'] = (~df['street'].isna()).astype(int)
        
        # Location quality score based on district
        district_scores = {
            'Центр': 5,
            'Пасічна': 4,
            'БАМ': 3,
            'Каскад': 4,
            'Залізничний (Вокзал)': 2,
            'Брати': 3,
            'Софіївка': 4,
            'Будівельників': 3,
            'Набережна': 5,
            'Опришівці': 2
        }
        df['location_score'] = df['district_filled'].map(district_scores).fillna(3)
        
        return df
    
    def _create_property_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create property characteristics features"""
        
        # Building type features
        df['building_type_filled'] = df['building_type'].fillna('квартира')
        building_dummies = pd.get_dummies(df['building_type_filled'], prefix='building')
        df = pd.concat([df, building_dummies], axis=1)
        
        # Renovation status features
        df['renovation_status_filled'] = df['renovation_status'].fillna('unknown')
        renovation_dummies = pd.get_dummies(df['renovation_status_filled'], prefix='renovation')
        df = pd.concat([df, renovation_dummies], axis=1)
        
        # Renovation quality score
        renovation_scores = {
            'євроремонт': 5,
            'дизайнерський': 5,
            'відмінний': 4,
            'хороший': 3,
            'косметичний': 2,
            'потребує ремонту': 1,
            'unknown': 2
        }
        df['renovation_score'] = df['renovation_status_filled'].map(renovation_scores).fillna(2)
        
        # Seller type features
        df['is_owner'] = (df['seller_type'] == 'owner').astype(int)
        df['is_agency'] = (df['seller_type'] == 'agency').astype(int)
        
        # Listing type features
        df['is_sale'] = (df['listing_type'] == 'sale').astype(int)
        df['is_rent'] = (df['listing_type'] == 'rent').astype(int)
        
        # Promoted listing
        df['is_promoted_int'] = df['is_promoted'].astype(int)
        
        return df
    
    def _create_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features from text fields"""
        
        # Title features
        df['title_length'] = df['title'].str.len().fillna(0)
        df['title_word_count'] = df['title'].str.split().str.len().fillna(0)
        
        # Description features
        df['description_length'] = df['description'].str.len().fillna(0)
        df['description_word_count'] = df['description'].str.split().str.len().fillna(0)
        df['has_description'] = (df['description_length'] > 0).astype(int)
        
        # Key words in title/description
        combined_text = (df['title'].fillna('') + ' ' + df['description'].fillna('')).str.lower()
        
        # Quality indicators
        quality_words = ['новий', 'новая', 'евроремонт', 'дизайнерский', 'люкс', 'элитный', 'premium']
        df['has_quality_words'] = combined_text.str.contains('|'.join(quality_words), na=False).astype(int)
        
        # Negative indicators
        negative_words = ['требует ремонт', 'потребує ремонт', 'старый', 'old', 'worn']
        df['has_negative_words'] = combined_text.str.contains('|'.join(negative_words), na=False).astype(int)
        
        # Amenities
        amenities = ['балкон', 'лоджия', 'кондиционер', 'parking', 'паркинг', 'лифт', 'охрана']
        df['amenities_count'] = combined_text.apply(
            lambda x: sum(1 for amenity in amenities if amenity in str(x))
        )
        
        return df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features"""
        
        # Convert scraped_at to datetime
        df['scraped_at'] = pd.to_datetime(df['scraped_at'])
        
        # Time-based features
        df['scraping_year'] = df['scraped_at'].dt.year
        df['scraping_month'] = df['scraped_at'].dt.month
        df['scraping_day_of_week'] = df['scraped_at'].dt.dayofweek
        df['scraping_day_of_month'] = df['scraped_at'].dt.day
        
        # Season
        df['season'] = df['scraping_month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'autumn', 10: 'autumn', 11: 'autumn'
        })
        season_dummies = pd.get_dummies(df['season'], prefix='season')
        df = pd.concat([df, season_dummies], axis=1)
        
        # Days since first scraping
        min_date = df['scraped_at'].min()
        df['days_since_start'] = (df['scraped_at'] - min_date).dt.days
        
        # Is weekend
        df['is_weekend'] = (df['scraping_day_of_week'].isin([5, 6])).astype(int)
        
        return df
    
    def _create_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create market-based features"""
        
        # Market statistics by district
        district_stats = df.groupby('district_filled').agg({
            'price_usd': ['mean', 'median', 'std', 'count'],
            'area': ['mean', 'median'],
            'price_per_sqm': ['mean', 'median']
        }).round(2)
        
        # Flatten column names
        district_stats.columns = ['_'.join(col).strip() for col in district_stats.columns]
        
        # Map to original dataframe
        for col in district_stats.columns:
            df[f'district_{col}'] = df['district_filled'].map(district_stats[col])
        
        # Price deviation from district average
        df['price_vs_district_avg'] = (
            df['price_usd'] / df['district_price_usd_mean']
        ).fillna(1)
        
        # Area deviation from district average
        df['area_vs_district_avg'] = (
            df['area'] / df['district_area_mean']
        ).fillna(1)
        
        # Market position
        df['is_expensive'] = (df['price_vs_district_avg'] > 1.2).astype(int)
        df['is_cheap'] = (df['price_vs_district_avg'] < 0.8).astype(int)
        
        # Supply indicators
        df['district_supply'] = df['district_filled'].map(
            df['district_filled'].value_counts()
        )
        
        return df
    
    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare final feature set"""
        
        # Fill numeric NaN values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Remove original text columns that are not needed for ML
        columns_to_drop = [
            'title', 'description', 'full_location', 'listing_url', 
            'image_url', 'posted_date', 'scraped_at', 'updated_at',
            'olx_id', 'street', 'district', 'building_type', 
            'renovation_status', 'seller_type', 'listing_type',
            'currency', 'season'  # Already encoded as dummies
        ]
        
        # Drop columns that exist
        columns_to_drop = [col for col in columns_to_drop if col in df.columns]
        df = df.drop(columns=columns_to_drop)
        
        # Remove infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        
        # Ensure target is clean
        if 'price_usd' in df.columns:
            df = df[df['price_usd'] > 0]  # Remove invalid prices
            df = df[df['price_usd'] < 1_000_000]  # Remove outliers
        
        return df
    
    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature names (excluding target)"""
        features = [col for col in df.columns if col != 'price_usd']
        return features
    
    def create_inference_features(self, property_data: Dict) -> pd.DataFrame:
        """
        Create features for a single property (inference)
        
        Args:
            property_data: Dictionary with property information
            
        Returns:
            pd.DataFrame: Feature vector for inference
        """
        # Convert to DataFrame
        df = pd.DataFrame([property_data])
        
        # Apply same feature engineering pipeline
        features_df = self.create_features(df)
        
        # Remove target if present
        if 'price_usd' in features_df.columns:
            features_df = features_df.drop(columns=['price_usd'])
        
        return features_df
