"""
Feature engineering for LightAutoML price prediction
===================================================

Prepares and transforms features for model training and inference.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering for real estate price prediction"""
    
    def __init__(self):
        self.district_encoder = {}
        self.street_encoder = {}
        self.building_type_encoder = {}
        self.renovation_encoder = {}
        self.seller_type_encoder = {}
        
        # Feature names for LightAutoML
        self.numeric_features = [
            'area_total', 'rooms', 'floor', 'floors_total',
            'price_per_sqm_area', 'floor_ratio', 'days_since_first_seen'
        ]
        
        self.categorical_features = [
            'district', 'street', 'building_type', 'renovation', 
            'seller_type', 'district_group', 'price_segment'
        ]
    
    def prepare_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Prepare features for model training or inference
        
        Args:
            df: Raw DataFrame
            is_training: Whether this is for training (affects encoding)
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Basic cleaning
        df = self._clean_data(df)
        
        # Create new features
        df = self._create_derived_features(df)
        df = self._create_categorical_features(df)
        df = self._create_temporal_features(df)
        
        # Encode categorical variables
        if is_training:
            df = self._fit_encoders(df)
        else:
            df = self._transform_with_encoders(df)
        
        # Select final features
        feature_columns = self.numeric_features + self.categorical_features
        
        # Ensure all required columns exist
        for col in feature_columns:
            if col not in df.columns:
                logger.warning(f"Missing feature column: {col}, filling with default")
                if col in self.numeric_features:
                    df[col] = 0.0
                else:
                    df[col] = 'unknown'
        
        # Return only feature columns + target if exists
        result_columns = feature_columns.copy()
        if 'price_value_usd' in df.columns:
            result_columns.append('price_value_usd')
        if 'ad_id' in df.columns:
            result_columns.append('ad_id')
            
        return df[result_columns]
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data"""
        df = df.copy()
        
        # Remove obvious outliers
        df = df[
            (df['area_total'] >= 15) & (df['area_total'] <= 300) &
            (df['price_value_usd'] >= 5000) & (df['price_value_usd'] <= 500000)
        ].copy()
        
        # Fill missing values
        df['rooms'] = df['rooms'].fillna(2)
        df['floor'] = df['floor'].fillna(1)
        df['floors_total'] = df['floors_total'].fillna(9)
        df['district'] = df['district'].fillna('Невідомий')
        df['street'] = df['street'].fillna('Невідома')
        df['building_type'] = df['building_type'].fillna('панель')
        df['renovation'] = df['renovation'].fillna('косметичний')
        df['seller_type'] = df['seller_type'].fillna('unknown')
        
        return df
    
    def _create_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived numeric features"""
        df = df.copy()
        
        # Price per square meter
        df['price_per_sqm_area'] = df['price_value_usd'] / df['area_total']
        
        # Floor ratio (relative floor position)
        df['floor_ratio'] = df['floor'] / df['floors_total'].clip(lower=1)
        
        return df
    
    def _create_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create categorical features"""
        df = df.copy()
        
        # District grouping (by popularity/prestige)
        district_groups = {
            'premium': ['Центр', 'Набережна'],
            'good': ['Каскад', 'Пасічна', 'Софіївка'],
            'standard': ['БАМ', 'Брати', 'Будівельників'],
            'budget': ['Залізничний (Вокзал)', 'Опришівці']
        }
        
        def get_district_group(district):
            for group, districts in district_groups.items():
                if district in districts:
                    return group
            return 'other'
        
        df['district_group'] = df['district'].apply(get_district_group)
        
        # Price segment based on area and location
        def get_price_segment(row):
            if pd.isna(row.get('price_value_usd')):
                return 'unknown'
            
            price = row['price_value_usd']
            area = row['area_total']
            district_group = row.get('district_group', 'other')
            
            if price < 30000:
                return 'budget'
            elif price < 60000:
                return 'standard'
            elif price < 100000:
                return 'premium'
            else:
                return 'luxury'
        
        df['price_segment'] = df.apply(get_price_segment, axis=1)
        
        return df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features"""
        df = df.copy()
        
        # Convert date columns to datetime
        for col in ['scraped_at', 'first_seen_at', 'last_seen_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Days since first seen (property age on market)
        if 'first_seen_at' in df.columns:
            reference_date = df['first_seen_at'].max()
            df['days_since_first_seen'] = (reference_date - df['first_seen_at']).dt.days
            df['days_since_first_seen'] = df['days_since_first_seen'].fillna(0)
        else:
            df['days_since_first_seen'] = 0
        
        return df
    
    def _fit_encoders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit categorical encoders on training data"""
        df = df.copy()
        
        # Simple label encoding with frequency-based ordering
        categorical_cols = {
            'district': self.district_encoder,
            'street': self.street_encoder, 
            'building_type': self.building_type_encoder,
            'renovation': self.renovation_encoder,
            'seller_type': self.seller_type_encoder
        }
        
        for col, encoder in categorical_cols.items():
            if col in df.columns:
                # Get value counts and create encoding based on frequency
                value_counts = df[col].value_counts()
                encoder.update({value: idx for idx, value in enumerate(value_counts.index)})
                
                # Transform the column
                df[col] = df[col].map(encoder).fillna(-1).astype(int)
                
                logger.info(f"Fitted encoder for {col}: {len(encoder)} unique values")
        
        return df
    
    def _transform_with_encoders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data using fitted encoders"""
        df = df.copy()
        
        categorical_cols = {
            'district': self.district_encoder,
            'street': self.street_encoder,
            'building_type': self.building_type_encoder, 
            'renovation': self.renovation_encoder,
            'seller_type': self.seller_type_encoder
        }
        
        for col, encoder in categorical_cols.items():
            if col in df.columns and encoder:
                df[col] = df[col].map(encoder).fillna(-1).astype(int)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        return self.numeric_features + self.categorical_features
    
    def prepare_single_sample(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare a single sample for prediction"""
        # Convert dict to DataFrame
        df = pd.DataFrame([data])
        
        # Add missing columns with defaults
        df['price_value_usd'] = np.nan  # Will be predicted
        df['first_seen_at'] = datetime.now()
        df['scraped_at'] = datetime.now()
        
        # Apply feature engineering
        df = self.prepare_features(df, is_training=False)
        
        return df

def prepare_features(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """
    Convenience function for feature preparation
    
    Args:
        df: Input DataFrame
        is_training: Whether this is training data
        
    Returns:
        DataFrame with engineered features
    """
    engineer = FeatureEngineer()
    return engineer.prepare_features(df, is_training)
