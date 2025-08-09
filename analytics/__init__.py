"""
Analytics Module for Property Monitor IF
Time series forecasting and market trend analysis
"""

from .prophet import (
    ProphetForecaster,
    generate_district_forecasts,
    TimeSeriesPreparator,
    create_forecast_visualizations,
    calculate_market_momentum
)

__all__ = [
    'ProphetForecaster',
    'generate_district_forecasts', 
    'TimeSeriesPreparator',
    'create_forecast_visualizations',
    'calculate_market_momentum'
]

__version__ = "1.0.0"
__description__ = "Analytics module for Property Monitor Ivano-Frankivsk"
