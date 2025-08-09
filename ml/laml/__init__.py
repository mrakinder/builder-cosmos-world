"""
LightAutoML Module - Module 2
Automated machine learning for property price prediction with real-time progress tracking
Target: MAPE ≤ 15%
"""

from .train import LightAutoMLTrainer, train_price_model
from .infer import PricePredictionInference, predict_property_price
from .features import FeatureEngineer
from .utils import ProgressTracker, ModelEvaluator, Logger, load_training_progress

__all__ = [
    'LightAutoMLTrainer',
    'train_price_model',
    'PricePredictionInference', 
    'predict_property_price',
    'FeatureEngineer',
    'ProgressTracker',
    'ModelEvaluator',
    'Logger',
    'load_training_progress'
]

__version__ = "1.0.0"
__author__ = "Property Monitor IF Team" 
__description__ = "LightAutoML for automated property price prediction with real-time progress tracking"
