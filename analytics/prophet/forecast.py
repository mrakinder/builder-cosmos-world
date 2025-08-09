"""
Prophet forecasting module
=========================

Creates price forecasts for districts using Facebook Prophet.
"""

import pandas as pd
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Prophet imports
try:
    from prophet import Prophet
    from prophet.plot import plot_plotly, plot_components_plotly
except ImportError:
    print("Prophet not installed. Installing...")
    import os
    os.system("pip install prophet")
    from prophet import Prophet
    from prophet.plot import plot_plotly, plot_components_plotly

from .prepare_series import prepare_prophet_data

logger = logging.getLogger(__name__)

class DistrictForecaster:
    """Handles Prophet forecasting for real estate districts"""
    
    def __init__(self, forecast_horizon: int = 6):
        self.forecast_horizon = forecast_horizon
        self.models = {}
        self.forecasts = {}
        self.model_metrics = {}
    
    def create_prophet_model(self, series_name: str, seasonal_patterns: bool = True) -> Prophet:
        """
        Create and configure Prophet model for a time series
        
        Args:
            series_name: Name of the time series (district_segment)
            seasonal_patterns: Whether to include seasonal components
            
        Returns:
            Configured Prophet model
        """
        # Configure Prophet model
        model_params = {
            'interval_width': 0.8,  # 80% confidence intervals
            'growth': 'linear',     # Linear growth assumption
            'daily_seasonality': False,
            'weekly_seasonality': False,
            'yearly_seasonality': seasonal_patterns,
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05,  # Flexibility of trend changes
            'seasonality_prior_scale': 10.0,  # Strength of seasonality
            'uncertainty_samples': 1000
        }
        
        model = Prophet(**model_params)
        
        # Add custom seasonalities if needed
        if seasonal_patterns:
            # Quarterly seasonality (real estate cycles)
            model.add_seasonality(
                name='quarterly',
                period=365.25/4,
                fourier_order=2
            )
        
        logger.debug(f"Created Prophet model for {series_name}")
        return model
    
    def fit_and_forecast(
        self, 
        series_name: str, 
        data: pd.DataFrame,
        include_history: bool = True
    ) -> pd.DataFrame:
        """
        Fit Prophet model and generate forecast
        
        Args:
            series_name: Name of the time series
            data: Prophet format DataFrame (ds, y)
            include_history: Whether to include historical period in forecast
            
        Returns:
            DataFrame with forecast results
        """
        try:
            # Create and fit model
            model = self.create_prophet_model(series_name)
            
            # Suppress Prophet's verbose output
            with_logging = logging.getLogger('prophet').level <= logging.INFO
            if not with_logging:
                logging.getLogger('prophet').setLevel(logging.WARNING)
            
            model.fit(data)
            
            # Create future dataframe
            future = model.make_future_dataframe(
                periods=self.forecast_horizon, 
                freq='M'
            )
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Store model and forecast
            self.models[series_name] = model
            
            # Add metadata to forecast
            forecast['series_name'] = series_name
            forecast['district'] = series_name.split('_')[0]
            forecast['segment'] = '_'.join(series_name.split('_')[1:]) if '_' in series_name else 'all'
            
            # Mark historical vs future periods
            last_historical_date = data['ds'].max()
            forecast['is_forecast'] = forecast['ds'] > last_historical_date
            
            # Calculate simple model metrics on historical data
            historical_forecast = forecast[forecast['ds'] <= last_historical_date].copy()
            if len(historical_forecast) > 0 and len(data) > 0:
                # Merge with actual data for metrics
                eval_data = historical_forecast.merge(data, on='ds', how='inner')
                if len(eval_data) > 0:
                    mae = abs(eval_data['yhat'] - eval_data['y']).mean()
                    mape = (abs(eval_data['yhat'] - eval_data['y']) / eval_data['y']).mean() * 100
                    
                    self.model_metrics[series_name] = {
                        'mae': mae,
                        'mape': mape,
                        'data_points': len(data),
                        'forecast_points': self.forecast_horizon
                    }
            
            logger.info(f"Forecast completed for {series_name}: {len(forecast)} total periods")
            return forecast
            
        except Exception as e:
            logger.error(f"Forecasting failed for {series_name}: {str(e)}")
            raise
    
    def forecast_all_districts(self, prophet_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Generate forecasts for all districts
        
        Args:
            prophet_data: Dictionary of Prophet-formatted DataFrames
            
        Returns:
            Combined DataFrame with all forecasts
        """
        all_forecasts = []
        successful_forecasts = 0
        
        logger.info(f"Starting forecasting for {len(prophet_data)} district-segments")
        
        for series_name, data in prophet_data.items():
            try:
                if len(data) < 3:
                    logger.warning(f"Insufficient data for {series_name}: {len(data)} points")
                    continue
                
                forecast = self.fit_and_forecast(series_name, data)
                all_forecasts.append(forecast)
                successful_forecasts += 1
                
                logger.debug(f"✅ {series_name}: forecast completed")
                
            except Exception as e:
                logger.error(f"❌ {series_name}: forecast failed - {str(e)}")
                continue
        
        if not all_forecasts:
            raise RuntimeError("No successful forecasts generated")
        
        # Combine all forecasts
        combined_forecast = pd.concat(all_forecasts, ignore_index=True)
        
        logger.info(f"Forecasting completed: {successful_forecasts}/{len(prophet_data)} successful")
        
        return combined_forecast
    
    def get_forecast_summary(self, forecast_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for forecasts"""
        
        # Overall summary
        total_districts = forecast_df['district'].nunique()
        total_segments = forecast_df['series_name'].nunique()
        
        # Future forecasts only
        future_forecasts = forecast_df[forecast_df['is_forecast'] == True].copy()
        
        # Price change analysis
        summary_stats = {}
        
        for series_name in forecast_df['series_name'].unique():
            series_data = forecast_df[forecast_df['series_name'] == series_name].copy()
            
            if len(series_data) > 0:
                # Last historical vs last forecast
                historical = series_data[series_data['is_forecast'] == False]
                future = series_data[series_data['is_forecast'] == True]
                
                if len(historical) > 0 and len(future) > 0:
                    last_historical_price = historical['yhat'].iloc[-1]
                    last_forecast_price = future['yhat'].iloc[-1]
                    
                    price_change_pct = ((last_forecast_price - last_historical_price) / last_historical_price) * 100
                    
                    summary_stats[series_name] = {
                        'district': series_data['district'].iloc[0],
                        'segment': series_data['segment'].iloc[0],
                        'current_price': round(last_historical_price, 0),
                        'forecast_price': round(last_forecast_price, 0),
                        'price_change_pct': round(price_change_pct, 1),
                        'trend': 'growing' if price_change_pct > 2 else 'declining' if price_change_pct < -2 else 'stable'
                    }
        
        return {
            'total_districts': total_districts,
            'total_segments': total_segments,
            'successful_forecasts': len(summary_stats),
            'forecast_horizon_months': self.forecast_horizon,
            'series_summary': summary_stats,
            'model_metrics': self.model_metrics
        }

def forecast_districts(
    time_series_path: str = 'analytics/time_series_data.csv',
    output_path: str = 'analytics/district_forecasts.csv',
    summary_path: str = 'analytics/forecast_summary.json',
    horizon: int = 6
) -> str:
    """
    Main forecasting function
    
    Args:
        time_series_path: Path to prepared time series data
        output_path: Where to save forecasts
        summary_path: Where to save forecast summary
        horizon: Forecast horizon in months
        
    Returns:
        Path to saved forecasts
    """
    logger.info(f"Starting Prophet forecasting with {horizon}-month horizon")
    
    try:
        # Load time series data
        logger.info(f"Loading time series data from {time_series_path}")
        monthly_df = pd.read_csv(time_series_path)
        monthly_df['ds'] = pd.to_datetime(monthly_df['ds'])
        
        if len(monthly_df) == 0:
            raise ValueError("No time series data found")
        
        # Prepare Prophet format data
        prophet_data = prepare_prophet_data(monthly_df, target_column='avg_price')
        
        if not prophet_data:
            raise ValueError("No valid time series found for forecasting")
        
        # Create forecaster and generate forecasts
        forecaster = DistrictForecaster(forecast_horizon=horizon)
        combined_forecast = forecaster.forecast_all_districts(prophet_data)
        
        # Generate summary
        summary = forecaster.get_forecast_summary(combined_forecast)
        
        # Save forecasts
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Select relevant columns for output
        output_columns = [
            'ds', 'yhat', 'yhat_lower', 'yhat_upper', 
            'series_name', 'district', 'segment', 'is_forecast'
        ]
        
        forecast_output = combined_forecast[output_columns].copy()
        forecast_output.to_csv(output_path, index=False, encoding='utf-8')
        
        # Save summary
        summary_path = Path(summary_path)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print results
        logger.info(f"Forecasting completed successfully:")
        logger.info(f"  - Districts forecasted: {summary['total_districts']}")
        logger.info(f"  - Segments forecasted: {summary['successful_forecasts']}")
        logger.info(f"  - Forecast horizon: {horizon} months")
        logger.info(f"  - Forecasts saved to: {output_path}")
        logger.info(f"  - Summary saved to: {summary_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Forecasting failed: {str(e)}")
        raise

def main():
    """CLI interface for Prophet forecasting"""
    parser = argparse.ArgumentParser(description='Generate Prophet forecasts for districts')
    parser.add_argument('--input', default='analytics/time_series_data.csv',
                       help='Input time series CSV file')
    parser.add_argument('--output', default='analytics/district_forecasts.csv',
                       help='Output forecasts CSV file')
    parser.add_argument('--summary', default='analytics/forecast_summary.json',
                       help='Output summary JSON file')
    parser.add_argument('--horizon', type=int, default=6,
                       help='Forecast horizon in months')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        output_path = forecast_districts(
            time_series_path=args.input,
            output_path=args.output,
            summary_path=args.summary,
            horizon=args.horizon
        )
        
        print(f"\n✅ Forecasting completed!")
        print(f"Forecasts saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Forecasting failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
