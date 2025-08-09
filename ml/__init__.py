"""
Machine Learning Module for Property Monitor IF
Automated ML and time series forecasting for real estate price analysis
"""

from .laml import (
    LightAutoMLTrainer, 
    train_price_model, 
    PricePredictionInference,
    predict_property_price,
    load_training_progress
)

__all__ = [
    'LightAutoMLTrainer',
    'train_price_model', 
    'PricePredictionInference',
    'predict_property_price',
    'load_training_progress'
]

__version__ = "1.0.0"
__description__ = "ML module for Property Monitor Ivano-Frankivsk"
