"""
Utility functions for Prophet forecasting module
Logging, evaluation, and helper functions
"""

import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error


class Logger:
    """Custom logger for Prophet module"""
    
    def __init__(self, log_file: str, level: str = "INFO"):
        self.logger = logging.getLogger("prophet_forecaster")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create log directory if not exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


class ForecastEvaluator:
    """
    Evaluate Prophet forecast performance
    """
    
    def __init__(self):
        pass
    
    def evaluate_forecast(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate forecast performance
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            
        Returns:
            Dict[str, float]: Evaluation metrics
        """
        try:
            if len(y_true) != len(y_pred) or len(y_true) == 0:
                return {}
            
            # Remove any NaN values
            mask = ~(np.isnan(y_true) | np.isnan(y_pred))
            y_true_clean = y_true[mask]
            y_pred_clean = y_pred[mask]
            
            if len(y_true_clean) == 0:
                return {}
            
            metrics = {}
            
            # Mean Absolute Error
            metrics['mae'] = round(float(mean_absolute_error(y_true_clean, y_pred_clean)), 2)
            
            # Root Mean Squared Error
            metrics['rmse'] = round(float(np.sqrt(mean_squared_error(y_true_clean, y_pred_clean))), 2)
            
            # Mean Absolute Percentage Error
            metrics['mape'] = round(float(mean_absolute_percentage_error(y_true_clean, y_pred_clean) * 100), 2)
            
            # Median Absolute Percentage Error
            ape = np.abs((y_true_clean - y_pred_clean) / y_true_clean) * 100
            metrics['median_ape'] = round(float(np.median(ape)), 2)
            
            # Mean Error (bias)
            metrics['mean_error'] = round(float(np.mean(y_pred_clean - y_true_clean)), 2)
            
            # R-squared (coefficient of determination)
            ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
            ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
            metrics['r2'] = round(float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0, 4)
            
            # Accuracy within 10% and 20%
            within_10_pct = np.mean(ape <= 10) * 100
            within_20_pct = np.mean(ape <= 20) * 100
            metrics['accuracy_10pct'] = round(float(within_10_pct), 1)
            metrics['accuracy_20pct'] = round(float(within_20_pct), 1)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def cross_validate_forecast(self, 
                               ts_data: pd.DataFrame,
                               prophet_model,
                               initial_periods: int = 12,
                               forecast_horizon: int = 6) -> Dict[str, Any]:
        """
        Perform cross-validation on Prophet forecast
        
        Args:
            ts_data: Time series data
            prophet_model: Trained Prophet model
            initial_periods: Initial training periods
            forecast_horizon: Forecast horizon for validation
            
        Returns:
            Dict[str, Any]: Cross-validation results
        """
        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            
            # Perform cross-validation
            df_cv = cross_validation(
                prophet_model,
                initial=f'{initial_periods * 30} days',  # Convert to days
                period=f'{forecast_horizon * 30} days',
                horizon=f'{forecast_horizon * 30} days'
            )
            
            # Calculate performance metrics
            df_p = performance_metrics(df_cv)
            
            # Aggregate metrics
            cv_results = {
                'mean_mape': round(float(df_p['mape'].mean() * 100), 2),
                'mean_mae': round(float(df_p['mae'].mean()), 2),
                'mean_rmse': round(float(df_p['rmse'].mean()), 2),
                'cv_periods': len(df_cv),
                'horizon_days': forecast_horizon * 30
            }
            
            return cv_results
            
        except Exception as e:
            return {'error': str(e)}


class TimeSeriesValidator:
    """
    Validate time series data quality
    """
    
    def __init__(self):
        pass
    
    def validate_data_quality(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate time series data quality
        
        Args:
            ts_data: Time series data with 'ds' and 'y' columns
            
        Returns:
            Dict[str, Any]: Data quality report
        """
        try:
            if ts_data is None or len(ts_data) == 0:
                return {'valid': False, 'error': 'Empty dataset'}
            
            # Check required columns
            required_cols = ['ds', 'y']
            missing_cols = [col for col in required_cols if col not in ts_data.columns]
            if missing_cols:
                return {'valid': False, 'error': f'Missing columns: {missing_cols}'}
            
            quality_report = {'valid': True}
            
            # Data completeness
            total_records = len(ts_data)
            missing_dates = ts_data['ds'].isna().sum()
            missing_values = ts_data['y'].isna().sum()
            
            quality_report['completeness'] = {
                'total_records': total_records,
                'missing_dates': int(missing_dates),
                'missing_values': int(missing_values),
                'completeness_rate': round((total_records - missing_values) / total_records * 100, 1)
            }
            
            # Data consistency
            ts_data_clean = ts_data.dropna()
            if len(ts_data_clean) > 0:
                
                # Date range and frequency
                date_range = ts_data_clean['ds'].max() - ts_data_clean['ds'].min()
                
                quality_report['consistency'] = {
                    'date_range_days': date_range.days,
                    'min_date': ts_data_clean['ds'].min().strftime('%Y-%m-%d'),
                    'max_date': ts_data_clean['ds'].max().strftime('%Y-%m-%d'),
                    'periods': len(ts_data_clean)
                }
                
                # Value distribution
                y_values = ts_data_clean['y']
                quality_report['distribution'] = {
                    'mean': round(float(y_values.mean()), 2),
                    'median': round(float(y_values.median()), 2),
                    'std': round(float(y_values.std()), 2),
                    'min': round(float(y_values.min()), 2),
                    'max': round(float(y_values.max()), 2),
                    'outliers_count': self._detect_outliers(y_values)
                }
                
                # Stationarity test (simplified)
                quality_report['stationarity'] = self._check_stationarity(y_values)
            
            # Recommendations
            quality_report['recommendations'] = self._generate_recommendations(quality_report)
            
            return quality_report
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _detect_outliers(self, values: pd.Series) -> int:
        """Detect outliers using IQR method"""
        try:
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = values[(values < lower_bound) | (values > upper_bound)]
            return len(outliers)
            
        except:
            return 0
    
    def _check_stationarity(self, values: pd.Series) -> Dict[str, Any]:
        """Simple stationarity check"""
        try:
            # Calculate rolling statistics
            window = min(len(values) // 4, 12)  # Quarterly or max 12 periods
            if window < 2:
                return {'status': 'insufficient_data'}
            
            rolling_mean = values.rolling(window=window).mean()
            rolling_std = values.rolling(window=window).std()
            
            # Check if rolling statistics are relatively stable
            mean_stability = rolling_mean.std() / values.mean() if values.mean() != 0 else float('inf')
            std_stability = rolling_std.std() / values.std() if values.std() != 0 else float('inf')
            
            is_stationary = mean_stability < 0.1 and std_stability < 0.1
            
            return {
                'status': 'stationary' if is_stationary else 'non_stationary',
                'mean_stability': round(float(mean_stability), 4),
                'std_stability': round(float(std_stability), 4)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        try:
            # Completeness recommendations
            completeness = quality_report.get('completeness', {})
            if completeness.get('completeness_rate', 100) < 80:
                recommendations.append("Низька повнота даних - розгляньте збільшення періоду збору даних")
            
            if completeness.get('missing_values', 0) > 0:
                recommendations.append("Є пропущені значення - застосуйте інтерполяцію або видаліть неповні записи")
            
            # Consistency recommendations
            consistency = quality_report.get('consistency', {})
            if consistency.get('periods', 0) < 12:
                recommendations.append("Недостатньо періодів для надійного прогнозування - потрібно мінімум 12 місяців")
            
            if consistency.get('date_range_days', 0) < 365:
                recommendations.append("Короткий період спостереження - для кращого прогнозу потрібен більший історичний період")
            
            # Distribution recommendations
            distribution = quality_report.get('distribution', {})
            outliers_count = distribution.get('outliers_count', 0)
            if outliers_count > 0:
                recommendations.append(f"Виявлено {outliers_count} викидів - розгляньте їх обробку")
            
            coefficient_of_variation = distribution.get('std', 0) / distribution.get('mean', 1)
            if coefficient_of_variation > 0.5:
                recommendations.append("Висока варіативність даних - розгляньте логарифмічне перетворення")
            
            # Stationarity recommendations
            stationarity = quality_report.get('stationarity', {})
            if stationarity.get('status') == 'non_stationary':
                recommendations.append("Дані нестаціонарні - Prophet автоматично оброблятиме тренд")
            
            if not recommendations:
                recommendations.append("Якість даних добра для прогнозування")
            
        except Exception as e:
            recommendations.append(f"Помилка генерації рекомендацій: {str(e)}")
        
        return recommendations


def prepare_district_comparison(forecasts: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare comparison table of district forecasts
    
    Args:
        forecasts: Forecast results by district
        
    Returns:
        pd.DataFrame: Comparison table
    """
    try:
        comparison_data = []
        
        for district, forecast_data in forecasts.items():
            if district.startswith('_'):  # Skip meta entries
                continue
            
            price_change = forecast_data.get('price_change_6m', {})
            trend = forecast_data.get('trend_analysis', {})
            
            comparison_data.append({
                'district': district,
                'current_price': forecast_data.get('current_price', 0),
                'predicted_price': price_change.get('predicted_price', 0),
                'price_change_usd': price_change.get('absolute_change', 0),
                'price_change_pct': price_change.get('percentage_change', 0),
                'trend_direction': trend.get('direction', 'unknown'),
                'confidence_interval': forecast_data.get('confidence_interval', 0.8),
                'historical_periods': forecast_data.get('historical_periods', 0),
                'forecast_date': forecast_data.get('forecast_date', '')
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Sort by price change percentage
        df = df.sort_values('price_change_pct', ascending=False)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


def calculate_market_momentum(forecasts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate overall market momentum indicators
    
    Args:
        forecasts: Forecast results by district
        
    Returns:
        Dict[str, Any]: Market momentum metrics
    """
    try:
        price_changes = []
        current_prices = []
        weights = []  # Weight by historical data availability
        
        for district, forecast_data in forecasts.items():
            if district.startswith('_'):
                continue
            
            price_change = forecast_data.get('price_change_6m', {})
            if 'percentage_change' in price_change:
                price_changes.append(price_change['percentage_change'])
                current_prices.append(forecast_data.get('current_price', 0))
                weights.append(forecast_data.get('historical_periods', 1))
        
        if not price_changes:
            return {}
        
        price_changes = np.array(price_changes)
        weights = np.array(weights)
        
        # Calculate weighted metrics
        weighted_avg_change = np.average(price_changes, weights=weights)
        
        momentum = {
            'overall_trend': 'bullish' if weighted_avg_change > 2 else 'bearish' if weighted_avg_change < -2 else 'neutral',
            'average_price_change': round(float(weighted_avg_change), 2),
            'market_volatility': round(float(np.std(price_changes)), 2),
            'districts_analyzed': len(price_changes),
            'growth_districts': int(np.sum(price_changes > 2)),
            'decline_districts': int(np.sum(price_changes < -2)),
            'stable_districts': int(np.sum((price_changes >= -2) & (price_changes <= 2))),
            'momentum_strength': 'strong' if abs(weighted_avg_change) > 5 else 'moderate' if abs(weighted_avg_change) > 2 else 'weak'
        }
        
        return momentum
        
    except Exception as e:
        return {'error': str(e)}


def export_forecast_summary(forecasts: Dict[str, Dict[str, Any]], 
                           output_path: str = "analytics/reports/forecast_summary.csv") -> bool:
    """
    Export forecast summary to CSV
    
    Args:
        forecasts: Forecast results
        output_path: Output file path
        
    Returns:
        bool: Success status
    """
    try:
        # Create comparison DataFrame
        df = prepare_district_comparison(forecasts)
        
        if df.empty:
            return False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        return True
        
    except Exception as e:
        return False
