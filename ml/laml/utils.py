"""
Utility functions for LightAutoML module
=======================================

Data loading, model persistence, and validation functions.
"""

import sqlite3
import pandas as pd
import pickle
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def load_data(source: str, path: str) -> pd.DataFrame:
    """
    Load data from SQLite database or CSV file
    
    Args:
        source: 'sqlite' or 'csv'
        path: Path to data source
        
    Returns:
        DataFrame with property data
    """
    try:
        if source == 'sqlite':
            return load_from_sqlite(path)
        elif source == 'csv':
            return load_from_csv(path)
        else:
            raise ValueError(f"Unsupported source: {source}")
    except Exception as e:
        logger.error(f"Error loading data from {source}:{path} - {str(e)}")
        raise

def load_from_sqlite(db_path: str) -> pd.DataFrame:
    """Load data from SQLite database"""
    query = """
    SELECT 
        ad_id,
        price_value as price_value_usd,
        price_currency,
        area_total,
        rooms,
        floor,
        floors_total,
        district,
        street,
        building_type,
        renovation,
        seller_type,
        location_text,
        description,
        scraped_at,
        first_seen_at,
        last_seen_at,
        is_active
    FROM offers 
    WHERE is_active = 1 
      AND price_value IS NOT NULL 
      AND price_currency = 'USD'
      AND area_total IS NOT NULL
      AND area_total > 0
    ORDER BY scraped_at ASC
    """
    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    
    logger.info(f"Loaded {len(df)} records from SQLite database")
    return df

def load_from_csv(csv_path: str) -> pd.DataFrame:
    """Load data from CSV file"""
    df = pd.read_csv(csv_path)
    
    # Filter for USD properties only
    df = df[
        (df['is_active'] == True) & 
        (df['price_currency'] == 'USD') &
        (df['price_value'].notna()) &
        (df['area_total'].notna()) &
        (df['area_total'] > 0)
    ].copy()
    
    logger.info(f"Loaded {len(df)} records from CSV file")
    return df

def split_data_by_time(df: pd.DataFrame, train_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data by time (older data for training, newer for validation)
    
    Args:
        df: DataFrame with scraped_at column
        train_ratio: Ratio of data for training
        
    Returns:
        Tuple of (train_df, val_df)
    """
    # Convert scraped_at to datetime if it's string
    df = df.copy()
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    
    # Sort by time
    df = df.sort_values('scraped_at')
    
    # Split by time
    split_idx = int(len(df) * train_ratio)
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()
    
    logger.info(f"Split data: {len(train_df)} train, {len(val_df)} validation samples")
    return train_df, val_df

def save_model(model, path: str, metadata: Dict[str, Any] = None):
    """Save trained model and metadata"""
    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save metadata
    if metadata:
        metadata_path = model_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Model saved to {model_path}")

def load_model(path: str):
    """Load trained model"""
    with open(path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Model loaded from {path}")
    return model

def validate_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean input data for prediction
    
    Args:
        data: Input property data
        
    Returns:
        Cleaned and validated data
    """
    required_fields = ['area_total', 'district']
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Clean and validate
    cleaned = {
        'area_total': float(data['area_total']),
        'district': str(data['district']),
        'rooms': int(data.get('rooms', 2)),
        'floor': int(data.get('floor', 1)),
        'floors_total': int(data.get('floors_total', 9)),
        'street': str(data.get('street', '')),
        'building_type': str(data.get('building_type', 'панель')),
        'renovation': str(data.get('renovation', 'косметичний')),
        'seller_type': str(data.get('seller_type', 'owner'))
    }
    
    # Validate ranges
    if cleaned['area_total'] <= 0 or cleaned['area_total'] > 500:
        raise ValueError("Invalid area_total: must be between 0 and 500")
    
    if cleaned['rooms'] < 1 or cleaned['rooms'] > 10:
        raise ValueError("Invalid rooms: must be between 1 and 10")
    
    if cleaned['floor'] < 1 or cleaned['floor'] > 50:
        raise ValueError("Invalid floor: must be between 1 and 50")
    
    return cleaned

def calculate_metrics(y_true, y_pred) -> Dict[str, float]:
    """Calculate prediction metrics"""
    import numpy as np
    from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
    
    # Remove any NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {'mape': float('inf'), 'rmse': float('inf'), 'mae': float('inf')}
    
    metrics = {
        'mape': mean_absolute_percentage_error(y_true_clean, y_pred_clean) * 100,
        'rmse': np.sqrt(mean_squared_error(y_true_clean, y_pred_clean)),
        'mae': np.mean(np.abs(y_true_clean - y_pred_clean)),
        'count': len(y_true_clean)
    }
    
    return metrics

def create_sample_request() -> Dict[str, Any]:
    """Create a sample request for testing"""
    return {
        "area_total": 65.0,
        "rooms": 2,
        "floor": 5,
        "floors_total": 9,
        "district": "Центр",
        "street": "Галицька",
        "building_type": "цегла",
        "renovation": "євроремонт",
        "seller_type": "owner"
    }
