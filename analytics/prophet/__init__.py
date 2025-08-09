"""
Prophet time series forecasting module
=====================================

Uses Facebook Prophet for price trend forecasting by districts.
"""

from .prepare_series import prepare_time_series
from .forecast import forecast_districts
from .plots import create_forecast_plots

__all__ = [
    "prepare_time_series",
    "forecast_districts", 
    "create_forecast_plots"
]
