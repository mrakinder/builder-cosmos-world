"""
Time series preparation for Prophet forecasting
==============================================

Prepares monthly price time series data for forecasting.
"""

import pandas as pd
import sqlite3
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

def load_price_data(db_path: str = 'data/olx_offers.sqlite') -> pd.DataFrame:
    """
    Load price data from SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        DataFrame with price data
    """
    query = """
    SELECT 
        ad_id,
        price_value as price_usd,
        price_currency,
        area_total,
        rooms,
        district,
        street,
        building_type,
        seller_type,
        scraped_at,
        first_seen_at,
        is_active
    FROM offers 
    WHERE is_active = 1 
      AND price_value IS NOT NULL 
      AND price_currency = 'USD'
      AND area_total IS NOT NULL
      AND area_total > 0
      AND district IS NOT NULL
      AND scraped_at IS NOT NULL
    ORDER BY scraped_at ASC
    """
    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    
    # Convert dates
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    df['first_seen_at'] = pd.to_datetime(df['first_seen_at'])
    
    logger.info(f"Loaded {len(df)} price records")
    return df

def create_monthly_series(df: pd.DataFrame, group_by: List[str] = None) -> pd.DataFrame:
    """
    Create monthly time series aggregated by district and optionally other dimensions
    
    Args:
        df: Input DataFrame with price data
        group_by: Additional grouping columns (e.g., ['rooms'])
        
    Returns:
        DataFrame with monthly time series
    """
    if group_by is None:
        group_by = []
    
    # Add month-year column
    df = df.copy()
    df['month_year'] = df['scraped_at'].dt.to_period('M')
    
    # Group by district and additional dimensions
    grouping_cols = ['district', 'month_year'] + group_by
    
    # Calculate monthly aggregations
    monthly_data = df.groupby(grouping_cols).agg({
        'price_usd': ['mean', 'median', 'count', 'std'],
        'area_total': 'mean',
        'ad_id': 'count'
    }).reset_index()
    
    # Flatten column names
    monthly_data.columns = [
        '_'.join(col).strip('_') if col[1] else col[0] 
        for col in monthly_data.columns
    ]
    
    # Rename columns for clarity
    monthly_data = monthly_data.rename(columns={
        'price_usd_mean': 'avg_price',
        'price_usd_median': 'median_price',
        'price_usd_count': 'price_count',
        'price_usd_std': 'price_std',
        'area_total_mean': 'avg_area',
        'ad_id_count': 'total_ads'
    })
    
    # Convert month_year to datetime for Prophet
    monthly_data['ds'] = monthly_data['month_year'].dt.to_timestamp()
    
    # Create segment identifier
    if group_by:
        monthly_data['segment'] = monthly_data[group_by].apply(
            lambda x: '_'.join([f"{col}_{val}" for col, val in zip(group_by, x)]), 
            axis=1
        )
    else:
        monthly_data['segment'] = 'all'
    
    logger.info(f"Created monthly series with {len(monthly_data)} data points")
    return monthly_data

def filter_districts_with_sufficient_data(
    df: pd.DataFrame, 
    min_months: int = 6,
    min_ads_per_month: int = 3
) -> pd.DataFrame:
    """
    Filter districts that have sufficient historical data for forecasting
    
    Args:
        df: Monthly time series DataFrame
        min_months: Minimum number of months required
        min_ads_per_month: Minimum ads per month on average
        
    Returns:
        Filtered DataFrame
    """
    # Calculate statistics per district-segment
    district_stats = df.groupby(['district', 'segment']).agg({
        'ds': 'count',
        'total_ads': 'mean',
        'avg_price': 'mean'
    }).reset_index()
    
    district_stats.columns = ['district', 'segment', 'months_count', 'avg_ads_per_month', 'avg_price_overall']
    
    # Filter districts with sufficient data
    valid_districts = district_stats[
        (district_stats['months_count'] >= min_months) &
        (district_stats['avg_ads_per_month'] >= min_ads_per_month)
    ][['district', 'segment']].copy()
    
    # Merge back to get filtered data
    filtered_df = df.merge(valid_districts, on=['district', 'segment'], how='inner')
    
    districts_kept = valid_districts['district'].nunique()
    segments_kept = len(valid_districts)
    
    logger.info(f"Filtered to {districts_kept} districts with {segments_kept} segments having sufficient data")
    logger.info(f"Criteria: ≥{min_months} months, ≥{min_ads_per_month} ads/month")
    
    return filtered_df

def prepare_prophet_data(
    monthly_df: pd.DataFrame,
    target_column: str = 'avg_price'
) -> Dict[str, pd.DataFrame]:
    """
    Prepare data in Prophet format (ds, y columns) grouped by district-segment
    
    Args:
        monthly_df: Monthly aggregated data
        target_column: Column to forecast
        
    Returns:
        Dictionary with district-segment as key and Prophet DataFrame as value
    """
    prophet_data = {}
    
    for (district, segment), group in monthly_df.groupby(['district', 'segment']):
        # Prepare Prophet format
        prophet_df = group[['ds', target_column]].copy()
        prophet_df.columns = ['ds', 'y']
        
        # Sort by date
        prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)
        
        # Remove any missing values
        prophet_df = prophet_df.dropna()
        
        if len(prophet_df) >= 6:  # Minimum data points for Prophet
            key = f"{district}_{segment}" if segment != 'all' else district
            prophet_data[key] = prophet_df
            
            logger.debug(f"Prepared {len(prophet_df)} data points for {key}")
    
    logger.info(f"Prepared Prophet data for {len(prophet_data)} district-segments")
    return prophet_data

def prepare_time_series(
    db_path: str = 'data/olx_offers.sqlite',
    output_path: str = 'analytics/time_series_data.csv',
    include_rooms_segment: bool = True,
    min_months: int = 6
) -> str:
    """
    Complete time series preparation pipeline
    
    Args:
        db_path: Path to SQLite database
        output_path: Where to save prepared time series
        include_rooms_segment: Whether to create room-based segments
        min_months: Minimum months of data required
        
    Returns:
        Path to saved time series data
    """
    logger.info("Starting time series preparation")
    
    # Load data
    df = load_price_data(db_path)
    
    if len(df) == 0:
        raise ValueError("No price data found in database")
    
    # Create monthly series
    group_by = ['rooms'] if include_rooms_segment else []
    monthly_df = create_monthly_series(df, group_by)
    
    # Filter districts with sufficient data
    filtered_df = filter_districts_with_sufficient_data(monthly_df, min_months)
    
    if len(filtered_df) == 0:
        raise ValueError(f"No districts have sufficient data (≥{min_months} months)")
    
    # Save prepared data
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    filtered_df.to_csv(output_path, index=False, encoding='utf-8')
    
    # Print summary
    districts_count = filtered_df['district'].nunique()
    segments_count = filtered_df.groupby(['district', 'segment']).ngroups
    date_range = f"{filtered_df['ds'].min().strftime('%Y-%m')} to {filtered_df['ds'].max().strftime('%Y-%m')}"
    
    logger.info(f"Time series preparation completed:")
    logger.info(f"  - Districts: {districts_count}")
    logger.info(f"  - Segments: {segments_count}")
    logger.info(f"  - Date range: {date_range}")
    logger.info(f"  - Saved to: {output_path}")
    
    return str(output_path)

def main():
    """CLI interface for time series preparation"""
    parser = argparse.ArgumentParser(description='Prepare time series data for Prophet forecasting')
    parser.add_argument('--db-path', default='data/olx_offers.sqlite',
                       help='Path to SQLite database')
    parser.add_argument('--output', default='analytics/time_series_data.csv',
                       help='Output CSV file path')
    parser.add_argument('--min-months', type=int, default=6,
                       help='Minimum months of data required per district')
    parser.add_argument('--include-rooms', action='store_true', default=True,
                       help='Include room-based segments')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        output_path = prepare_time_series(
            db_path=args.db_path,
            output_path=args.output,
            include_rooms_segment=args.include_rooms,
            min_months=args.min_months
        )
        
        print(f"\n✅ Time series preparation completed!")
        print(f"Data saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Time series preparation failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
