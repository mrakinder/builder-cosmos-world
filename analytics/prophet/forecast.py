"""
Prophet Forecasting Module - Module 3
6-month price trend forecasting by districts using Facebook Prophet
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Prophet imports
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.graph_objects as go
import plotly.express as px

from .prepare_series import TimeSeriesPreparator
from .utils import Logger, ForecastEvaluator


class ProphetForecaster:
    """
    Prophet-based forecasting for real estate price trends
    """
    
    def __init__(self, forecast_periods: int = 6):
        self.forecast_periods = forecast_periods  # months
        self.logger = Logger("analytics/reports/prophet_forecast.log")
        self.preparator = TimeSeriesPreparator()
        self.evaluator = ForecastEvaluator()
        
        # Prophet models by district
        self.models = {}
        self.forecasts = {}
        
    def forecast_all_districts(self, 
                              districts: List[str] = None,
                              confidence_interval: float = 0.8) -> Dict[str, Dict[str, Any]]:
        """
        Generate forecasts for all districts
        
        Args:
            districts: List of districts to forecast (None for all)
            confidence_interval: Confidence interval for forecasts
            
        Returns:
            Dict[str, Dict[str, Any]]: Forecasts by district
        """
        try:
            self.logger.info(f"🔮 Starting Prophet forecasting for {self.forecast_periods} months...")
            
            # Prepare time series data
            district_series = self.preparator.prepare_district_series(districts)
            
            if not district_series:
                self.logger.warning("⚠️ No time series data available for forecasting")
                return {}
            
            forecasts_result = {}
            
            for district, ts_data in district_series.items():
                try:
                    self.logger.info(f"🏘️ Forecasting for {district}...")
                    
                    forecast_result = self._forecast_single_district(
                        district, ts_data, confidence_interval
                    )
                    
                    if forecast_result:
                        forecasts_result[district] = forecast_result
                        self.logger.info(f"✅ {district}: forecast completed")
                    else:
                        self.logger.warning(f"⚠️ {district}: forecast failed")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error forecasting {district}: {str(e)}")
                    continue
            
            # Generate summary forecast
            if forecasts_result:
                summary = self._generate_forecast_summary(forecasts_result)
                forecasts_result['_summary'] = summary
            
            self.logger.info(f"✅ Forecasting completed for {len(forecasts_result)} districts")
            return forecasts_result
            
        except Exception as e:
            self.logger.error(f"❌ Error in forecast_all_districts: {str(e)}")
            return {}
    
    def _forecast_single_district(self, 
                                 district: str, 
                                 ts_data: pd.DataFrame,
                                 confidence_interval: float) -> Optional[Dict[str, Any]]:
        """Forecast for a single district"""
        try:
            # Prepare data for Prophet
            prophet_data = ts_data[['ds', 'y']].copy()
            prophet_data = prophet_data.dropna()
            
            if len(prophet_data) < 3:
                self.logger.warning(f"⚠️ {district}: insufficient data points ({len(prophet_data)})")
                return None
            
            # Initialize Prophet model
            model = Prophet(
                interval_width=confidence_interval,
                changepoint_prior_scale=0.1,
                seasonality_prior_scale=0.1,
                holidays_prior_scale=0.1,
                daily_seasonality=False,
                weekly_seasonality=False,
                yearly_seasonality=True
            )
            
            # Add custom seasonalities for real estate market
            model.add_seasonality(
                name='quarterly',
                period=365.25/4,
                fourier_order=2
            )
            
            # Fit model
            model.fit(prophet_data)
            
            # Create future dataframe
            future = model.make_future_dataframe(
                periods=self.forecast_periods,
                freq='M'
            )
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Store model
            self.models[district] = model
            self.forecasts[district] = forecast
            
            # Extract forecast results
            forecast_result = self._extract_forecast_results(
                district, prophet_data, forecast, ts_data
            )
            
            return forecast_result
            
        except Exception as e:
            self.logger.error(f"❌ Error forecasting {district}: {str(e)}")
            return None
    
    def _extract_forecast_results(self, 
                                 district: str, 
                                 historical_data: pd.DataFrame,
                                 forecast: pd.DataFrame,
                                 original_data: pd.DataFrame) -> Dict[str, Any]:
        """Extract and format forecast results"""
        try:
            # Split historical and future
            n_historical = len(historical_data)
            historical_forecast = forecast.iloc[:n_historical]
            future_forecast = forecast.iloc[n_historical:]
            
            # Calculate historical performance metrics
            if len(historical_data) > 1:
                historical_performance = self.evaluator.evaluate_forecast(
                    historical_data['y'].values,
                    historical_forecast['yhat'].values
                )
            else:
                historical_performance = {}
            
            # Format future predictions
            future_predictions = []
            for _, row in future_forecast.iterrows():
                prediction = {
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_price': round(float(row['yhat']), 2),
                    'lower_bound': round(float(row['yhat_lower']), 2),
                    'upper_bound': round(float(row['yhat_upper']), 2),
                    'trend': round(float(row['trend']), 2),
                    'seasonal': round(float(row.get('seasonal', 0)), 2)
                }
                future_predictions.append(prediction)
            
            # Calculate trend analysis
            trend_analysis = self._analyze_trend(forecast)
            
            # Market insights
            insights = self._generate_insights(district, historical_data, future_forecast, original_data)
            
            result = {
                'district': district,
                'forecast_horizon_months': self.forecast_periods,
                'historical_periods': len(historical_data),
                'future_predictions': future_predictions,
                'trend_analysis': trend_analysis,
                'historical_performance': historical_performance,
                'insights': insights,
                'forecast_date': datetime.now().isoformat(),
                'current_price': round(float(historical_data['y'].iloc[-1]), 2) if len(historical_data) > 0 else None,
                'price_change_6m': self._calculate_price_change(historical_data, future_forecast),
                'confidence_interval': 0.8
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting forecast results for {district}: {str(e)}")
            return {}
    
    def _analyze_trend(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend from forecast"""
        try:
            trends = forecast['trend'].values
            
            # Overall trend direction
            if len(trends) < 2:
                return {'direction': 'unknown', 'strength': 0}
            
            trend_change = trends[-1] - trends[0]
            trend_pct = (trend_change / trends[0]) * 100
            
            # Determine trend direction
            if trend_pct > 2:
                direction = 'increasing'
            elif trend_pct < -2:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            # Trend strength (volatility)
            trend_volatility = np.std(np.diff(trends))
            
            return {
                'direction': direction,
                'change_percent': round(trend_pct, 2),
                'strength': round(trend_volatility, 2),
                'trend_start': round(float(trends[0]), 2),
                'trend_end': round(float(trends[-1]), 2)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing trend: {str(e)}")
            return {'direction': 'unknown', 'strength': 0}
    
    def _generate_insights(self, 
                          district: str, 
                          historical_data: pd.DataFrame,
                          future_forecast: pd.DataFrame,
                          original_data: pd.DataFrame) -> List[str]:
        """Generate market insights from forecast"""
        insights = []
        
        try:
            if len(historical_data) == 0 or len(future_forecast) == 0:
                return ["Insufficient data for insights generation"]
            
            current_price = historical_data['y'].iloc[-1]
            future_price = future_forecast['yhat'].iloc[-1]
            price_change = ((future_price - current_price) / current_price) * 100
            
            # Price trend insights
            if price_change > 10:
                insights.append(f"Очікується значне зростання цін у районі {district} на {price_change:.1f}% протягом 6 місяців")
            elif price_change > 5:
                insights.append(f"Прогнозується помірне зростання цін у районі {district} на {price_change:.1f}%")
            elif price_change < -10:
                insights.append(f"Очікується суттєве зниження цін у районі {district} на {abs(price_change):.1f}%")
            elif price_change < -5:
                insights.append(f"Прогнозується помірне зниження цін у районі {district} на {abs(price_change):.1f}%")
            else:
                insights.append(f"Ціни у районі {district} залишаться стабільними (зміна {price_change:.1f}%)")
            
            # Market activity insights
            if 'volume' in original_data.columns:
                avg_volume = original_data['volume'].mean()
                recent_volume = original_data['volume'].iloc[-3:].mean() if len(original_data) >= 3 else avg_volume
                
                if recent_volume > avg_volume * 1.2:
                    insights.append(f"Висока активність на ринку {district} - кількість пропозицій зросла")
                elif recent_volume < avg_volume * 0.8:
                    insights.append(f"Знижена активність на ринку {district} - мало нових пропозицій")
            
            # Seasonality insights
            future_months = future_forecast['ds'].dt.month
            if any(month in [5, 6, 7, 8] for month in future_months):
                insights.append("Літні місяці традиційно активні для ринку нерухомості")
            if any(month in [11, 12, 1, 2] for month in future_months):
                insights.append("Зимовий період може характеризуватися нижчою активністю")
            
            # Price range insights
            price_range = (future_forecast['yhat_upper'].iloc[-1] - future_forecast['yhat_lower'].iloc[-1])
            uncertainty_pct = (price_range / future_price) * 100
            
            if uncertainty_pct > 30:
                insights.append(f"Висока невизначеність прогнозу для {district} - широкий діапазон можливих цін")
            elif uncertainty_pct < 15:
                insights.append(f"Стабільний прогноз для {district} - низька волатильність очікується")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ Error generating insights: {str(e)}")
            return ["Помилка при генерації аналітичних висновків"]
    
    def _calculate_price_change(self, 
                               historical_data: pd.DataFrame,
                               future_forecast: pd.DataFrame) -> Dict[str, float]:
        """Calculate price changes over forecast period"""
        try:
            if len(historical_data) == 0 or len(future_forecast) == 0:
                return {}
            
            current_price = historical_data['y'].iloc[-1]
            future_price = future_forecast['yhat'].iloc[-1]
            
            absolute_change = future_price - current_price
            percentage_change = (absolute_change / current_price) * 100
            
            return {
                'absolute_change': round(float(absolute_change), 2),
                'percentage_change': round(float(percentage_change), 2),
                'current_price': round(float(current_price), 2),
                'predicted_price': round(float(future_price), 2)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating price change: {str(e)}")
            return {}
    
    def _generate_forecast_summary(self, forecasts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary across all district forecasts"""
        try:
            if not forecasts:
                return {}
            
            # Aggregate statistics
            all_changes = []
            district_summaries = []
            
            for district, forecast_data in forecasts.items():
                if district.startswith('_'):  # Skip meta entries
                    continue
                
                price_change = forecast_data.get('price_change_6m', {})
                if 'percentage_change' in price_change:
                    all_changes.append(price_change['percentage_change'])
                
                district_summaries.append({
                    'district': district,
                    'current_price': forecast_data.get('current_price'),
                    'predicted_change': price_change.get('percentage_change', 0),
                    'trend_direction': forecast_data.get('trend_analysis', {}).get('direction', 'unknown')
                })
            
            # Market overview
            if all_changes:
                market_summary = {
                    'total_districts': len(forecasts),
                    'average_price_change': round(np.mean(all_changes), 2),
                    'price_change_range': {
                        'min': round(min(all_changes), 2),
                        'max': round(max(all_changes), 2)
                    },
                    'districts_growing': len([x for x in all_changes if x > 2]),
                    'districts_declining': len([x for x in all_changes if x < -2]),
                    'districts_stable': len([x for x in all_changes if -2 <= x <= 2]),
                    'forecast_date': datetime.now().isoformat(),
                    'forecast_horizon': f"{self.forecast_periods} months"
                }
            else:
                market_summary = {
                    'total_districts': 0,
                    'error': 'No valid forecasts generated'
                }
            
            return market_summary
            
        except Exception as e:
            self.logger.error(f"❌ Error generating forecast summary: {str(e)}")
            return {'error': str(e)}
    
    def export_forecasts(self, forecasts: Dict[str, Dict[str, Any]], 
                        output_path: str = "analytics/reports/district_forecasts.json"):
        """Export forecasts to file"""
        try:
            import json
            
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(forecasts, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📊 Forecasts exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting forecasts: {str(e)}")


def generate_district_forecasts(districts: List[str] = None, 
                               forecast_months: int = 6,
                               export: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Main entry point for generating district forecasts
    
    Args:
        districts: List of districts to forecast
        forecast_months: Number of months to forecast
        export: Whether to export results to file
        
    Returns:
        Dict[str, Dict[str, Any]]: Forecast results by district
    """
    forecaster = ProphetForecaster(forecast_periods=forecast_months)
    forecasts = forecaster.forecast_all_districts(districts)
    
    if export and forecasts:
        forecaster.export_forecasts(forecasts)
    
    return forecasts


if __name__ == "__main__":
    # Test forecasting
    forecaster = ProphetForecaster(forecast_periods=6)
    
    # Generate forecasts for all districts
    forecasts = forecaster.forecast_all_districts()
    
    print(f"Generated forecasts for {len(forecasts)} districts")
    
    for district, forecast_data in forecasts.items():
        if not district.startswith('_'):
            price_change = forecast_data.get('price_change_6m', {})
            change_pct = price_change.get('percentage_change', 0)
            print(f"{district}: {change_pct:+.1f}% expected change")
