"""
Prophet Time Series Forecasting Module - Module 3
6-month price trend forecasting by districts using Facebook Prophet
"""

from .prepare_series import TimeSeriesPreparator, prepare_prophet_data
from .forecast import ProphetForecaster, generate_district_forecasts
from .plots import ProphetPlotter, create_forecast_visualizations
from .utils import (
    Logger, 
    ForecastEvaluator, 
    TimeSeriesValidator,
    prepare_district_comparison,
    calculate_market_momentum,
    export_forecast_summary
)

__all__ = [
    'TimeSeriesPreparator',
    'prepare_prophet_data',
    'ProphetForecaster', 
    'generate_district_forecasts',
    'ProphetPlotter',
    'create_forecast_visualizations',
    'Logger',
    'ForecastEvaluator',
    'TimeSeriesValidator',
    'prepare_district_comparison',
    'calculate_market_momentum',
    'export_forecast_summary'
]

__version__ = "1.0.0"
__author__ = "Property Monitor IF Team"
__description__ = "Prophet time series forecasting for real estate price trends by districts"
