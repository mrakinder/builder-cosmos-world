"""
Prophet Time Series Preparation Module - Module 3
Prepares time series data for Prophet forecasting by districts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import os

from .utils import Logger


class TimeSeriesPreparator:
    """
    Prepares time series data for Prophet forecasting
    Aggregates property data by district and time period
    """
    
    def __init__(self, db_path: str = "data/olx_offers.sqlite"):
        self.db_path = db_path
        self.logger = Logger("analytics/reports/prophet_prep.log")
        
    def prepare_district_series(self, 
                               districts: List[str] = None,
                               min_samples_per_period: int = 5,
                               period: str = "monthly") -> Dict[str, pd.DataFrame]:
        """
        Prepare time series data for each district
        
        Args:
            districts: List of districts to process (None for all)
            min_samples_per_period: Minimum samples required per time period
            period: Aggregation period ('daily', 'weekly', 'monthly')
            
        Returns:
            Dict[str, pd.DataFrame]: Time series data by district
        """
        try:
            self.logger.info(f"🔄 Preparing {period} time series data for districts...")
            
            # Load property data
            df = self._load_property_data()
            
            if df is None or len(df) == 0:
                self.logger.warning("⚠️ No property data available")
                return {}
            
            # Filter districts if specified
            if districts:
                df = df[df['district'].isin(districts)]
            
            # Get unique districts
            available_districts = df['district'].unique()
            self.logger.info(f"📊 Processing {len(available_districts)} districts")
            
            district_series = {}
            
            for district in available_districts:
                try:
                    district_data = df[df['district'] == district].copy()
                    
                    if len(district_data) < min_samples_per_period:
                        self.logger.warning(f"⚠️ Skipping {district}: insufficient data ({len(district_data)} samples)")
                        continue
                    
                    # Prepare time series for this district
                    ts_data = self._create_time_series(district_data, period)
                    
                    if ts_data is not None and len(ts_data) >= 3:  # Minimum periods for Prophet
                        district_series[district] = ts_data
                        self.logger.info(f"✅ {district}: {len(ts_data)} time periods")
                    else:
                        self.logger.warning(f"⚠️ Skipping {district}: insufficient time periods")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing {district}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Prepared time series for {len(district_series)} districts")
            return district_series
            
        except Exception as e:
            self.logger.error(f"❌ Error preparing district series: {str(e)}")
            return {}
    
    def _load_property_data(self) -> Optional[pd.DataFrame]:
        """Load property data from database"""
        try:
            if not os.path.exists(self.db_path):
                self.logger.error(f"❌ Database not found: {self.db_path}")
                return None
            
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                district,
                price_usd,
                area,
                rooms,
                floor,
                total_floors,
                seller_type,
                listing_type,
                scraped_at,
                building_type,
                renovation_status
            FROM properties 
            WHERE is_active = 1 
            AND price_usd IS NOT NULL 
            AND price_usd > 0 
            AND district IS NOT NULL
            AND currency = 'USD'
            ORDER BY scraped_at ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert scraped_at to datetime
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            
            # Filter reasonable price range
            df = df[
                (df['price_usd'] >= 10000) & 
                (df['price_usd'] <= 500000)
            ]
            
            self.logger.info(f"📊 Loaded {len(df)} property records")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error loading property data: {str(e)}")
            return None
    
    def _create_time_series(self, district_data: pd.DataFrame, period: str) -> Optional[pd.DataFrame]:
        """Create time series for a specific district"""
        try:
            # Set date as index
            df = district_data.copy()
            df = df.set_index('scraped_at').sort_index()
            
            # Determine aggregation frequency
            freq_map = {
                'daily': 'D',
                'weekly': 'W',
                'monthly': 'M'
            }
            freq = freq_map.get(period, 'M')
            
            # Aggregate by time period
            agg_funcs = {
                'price_usd': ['mean', 'median', 'count', 'std'],
                'area': ['mean', 'median'],
                'rooms': ['mean'],
                'floor': ['mean']
            }
            
            ts_data = df.resample(freq).agg(agg_funcs).round(2)
            
            # Flatten column names
            ts_data.columns = ['_'.join(col).strip() for col in ts_data.columns]
            
            # Filter periods with sufficient data
            min_count = 3 if period == 'monthly' else 5
            ts_data = ts_data[ts_data['price_usd_count'] >= min_count]
            
            if len(ts_data) == 0:
                return None
            
            # Reset index and rename for Prophet
            ts_data = ts_data.reset_index()
            ts_data = ts_data.rename(columns={'scraped_at': 'ds'})
            
            # Create main target variable (y) - median price
            ts_data['y'] = ts_data['price_usd_median']
            
            # Add additional metrics
            ts_data['price_per_sqm'] = ts_data['price_usd_median'] / ts_data['area_median']
            ts_data['volume'] = ts_data['price_usd_count']  # Number of listings
            
            # Remove rows with NaN in target
            ts_data = ts_data.dropna(subset=['y'])
            
            return ts_data
            
        except Exception as e:
            self.logger.error(f"❌ Error creating time series: {str(e)}")
            return None
    
    def prepare_market_overview_series(self) -> Optional[pd.DataFrame]:
        """Prepare overall market time series (all districts combined)"""
        try:
            self.logger.info("🔄 Preparing market overview time series...")
            
            df = self._load_property_data()
            
            if df is None or len(df) == 0:
                return None
            
            # Create overall market time series
            market_ts = self._create_time_series(df, 'monthly')
            
            if market_ts is not None:
                self.logger.info(f"✅ Market overview series: {len(market_ts)} periods")
            
            return market_ts
            
        except Exception as e:
            self.logger.error(f"❌ Error preparing market overview: {str(e)}")
            return None
    
    def prepare_segment_series(self, 
                              segment_by: str = "rooms",
                              districts: List[str] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Prepare time series segmented by property characteristics
        
        Args:
            segment_by: Segmentation variable ('rooms', 'building_type', 'seller_type')
            districts: Districts to include
            
        Returns:
            Dict[str, Dict[str, pd.DataFrame]]: Nested dict {district: {segment: time_series}}
        """
        try:
            self.logger.info(f"🔄 Preparing segmented time series by {segment_by}...")
            
            df = self._load_property_data()
            
            if df is None or len(df) == 0:
                return {}
            
            # Filter districts if specified
            if districts:
                df = df[df['district'].isin(districts)]
            
            # Clean segment variable
            if segment_by == 'rooms':
                df['rooms'] = df['rooms'].fillna(2).astype(int)
                df['segment'] = df['rooms'].apply(lambda x: f"{x}_rooms" if x <= 4 else "5+_rooms")
            elif segment_by == 'building_type':
                df['segment'] = df['building_type'].fillna('квартира')
            elif segment_by == 'seller_type':
                df['segment'] = df['seller_type'].fillna('agency')
            else:
                self.logger.error(f"❌ Unknown segment_by: {segment_by}")
                return {}
            
            result = {}
            
            for district in df['district'].unique():
                district_data = df[df['district'] == district]
                district_result = {}
                
                for segment in district_data['segment'].unique():
                    segment_data = district_data[district_data['segment'] == segment]
                    
                    if len(segment_data) >= 10:  # Minimum for segmentation
                        ts_data = self._create_time_series(segment_data, 'monthly')
                        if ts_data is not None and len(ts_data) >= 3:
                            district_result[str(segment)] = ts_data
                
                if district_result:
                    result[district] = district_result
            
            self.logger.info(f"✅ Prepared segmented series for {len(result)} districts")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error preparing segment series: {str(e)}")
            return {}
    
    def get_data_summary(self) -> Dict[str, any]:
        """Get summary statistics of available data"""
        try:
            df = self._load_property_data()
            
            if df is None or len(df) == 0:
                return {}
            
            summary = {
                'total_properties': len(df),
                'date_range': {
                    'start': df['scraped_at'].min().isoformat(),
                    'end': df['scraped_at'].max().isoformat(),
                    'days': (df['scraped_at'].max() - df['scraped_at'].min()).days
                },
                'districts': {
                    'count': df['district'].nunique(),
                    'list': df['district'].unique().tolist(),
                    'properties_per_district': df['district'].value_counts().to_dict()
                },
                'price_stats': {
                    'mean': round(df['price_usd'].mean(), 2),
                    'median': round(df['price_usd'].median(), 2),
                    'min': round(df['price_usd'].min(), 2),
                    'max': round(df['price_usd'].max(), 2),
                    'std': round(df['price_usd'].std(), 2)
                },
                'data_quality': {
                    'missing_prices': int(df['price_usd'].isna().sum()),
                    'missing_districts': int(df['district'].isna().sum()),
                    'missing_areas': int(df['area'].isna().sum())
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error generating data summary: {str(e)}")
            return {}


def prepare_prophet_data(districts: List[str] = None, 
                        period: str = "monthly") -> Dict[str, pd.DataFrame]:
    """
    Main entry point for preparing Prophet time series data
    
    Args:
        districts: List of districts to process
        period: Time aggregation period
        
    Returns:
        Dict[str, pd.DataFrame]: Time series data by district
    """
    preparator = TimeSeriesPreparator()
    return preparator.prepare_district_series(districts, period=period)


if __name__ == "__main__":
    # Test data preparation
    preparator = TimeSeriesPreparator()
    
    # Get data summary
    summary = preparator.get_data_summary()
    print(f"Data summary: {summary}")
    
    # Prepare district series
    district_series = preparator.prepare_district_series()
    print(f"Prepared series for {len(district_series)} districts")
    
    for district, data in district_series.items():
        print(f"{district}: {len(data)} periods")
