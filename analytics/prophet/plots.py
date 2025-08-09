"""
Prophet Plotting and Visualization Module
Creates charts and visualizations for forecasting results
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

from .utils import Logger


class ProphetPlotter:
    """
    Creates visualizations for Prophet forecasting results
    """
    
    def __init__(self, output_dir: str = "reports/prophet"):
        self.output_dir = output_dir
        self.logger = Logger("analytics/reports/prophet_plots.log")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def plot_district_forecast(self, 
                              district: str,
                              historical_data: pd.DataFrame,
                              forecast_data: pd.DataFrame,
                              save: bool = True) -> Optional[str]:
        """
        Plot forecast for a single district
        
        Args:
            district: District name
            historical_data: Historical time series data
            forecast_data: Prophet forecast results
            save: Whether to save the plot
            
        Returns:
            Optional[str]: Path to saved plot file
        """
        try:
            self.logger.info(f"📊 Creating forecast plot for {district}...")
            
            # Create plotly figure
            fig = go.Figure()
            
            # Historical data
            if len(historical_data) > 0:
                fig.add_trace(go.Scatter(
                    x=historical_data['ds'],
                    y=historical_data['y'],
                    mode='lines+markers',
                    name='Історичні дані',
                    line=dict(color='blue', width=2),
                    marker=dict(size=6)
                ))
            
            # Forecast line
            fig.add_trace(go.Scatter(
                x=forecast_data['ds'],
                y=forecast_data['yhat'],
                mode='lines',
                name='Прогноз',
                line=dict(color='red', width=2)
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=forecast_data['ds'],
                y=forecast_data['yhat_upper'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_data['ds'],
                y=forecast_data['yhat_lower'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(255, 0, 0, 0.2)',
                fill='tonexty',
                name='Довірчий інтервал',
                hoverinfo='skip'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'Прогноз цін на нерухомість - {district}',
                xaxis_title='Дата',
                yaxis_title='Ціна (USD)',
                hovermode='x unified',
                template='plotly_white',
                width=1000,
                height=600,
                font=dict(size=12)
            )
            
            # Add vertical line at forecast start
            if len(historical_data) > 0:
                forecast_start = historical_data['ds'].iloc[-1]
                fig.add_vline(
                    x=forecast_start,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Початок прогнозу"
                )
            
            if save:
                filename = f"{district.replace(' ', '_').replace('(', '').replace(')', '')}_forecast.html"
                filepath = os.path.join(self.output_dir, filename)
                fig.write_html(filepath)
                self.logger.info(f"✅ Forecast plot saved: {filepath}")
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error creating forecast plot for {district}: {str(e)}")
            return None
    
    def plot_components(self, 
                       district: str,
                       forecast_data: pd.DataFrame,
                       save: bool = True) -> Optional[str]:
        """
        Plot Prophet forecast components (trend, seasonality)
        
        Args:
            district: District name
            forecast_data: Prophet forecast results
            save: Whether to save the plot
            
        Returns:
            Optional[str]: Path to saved plot file
        """
        try:
            self.logger.info(f"📊 Creating components plot for {district}...")
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=['Тренд', 'Річна сезонність', 'Квартальна сезонність'],
                vertical_spacing=0.1
            )
            
            # Trend
            fig.add_trace(go.Scatter(
                x=forecast_data['ds'],
                y=forecast_data['trend'],
                mode='lines',
                name='Тренд',
                line=dict(color='blue', width=2)
            ), row=1, col=1)
            
            # Yearly seasonality
            if 'yearly' in forecast_data.columns:
                fig.add_trace(go.Scatter(
                    x=forecast_data['ds'],
                    y=forecast_data['yearly'],
                    mode='lines',
                    name='Річна сезонність',
                    line=dict(color='green', width=2)
                ), row=2, col=1)
            
            # Quarterly seasonality
            if 'quarterly' in forecast_data.columns:
                fig.add_trace(go.Scatter(
                    x=forecast_data['ds'],
                    y=forecast_data['quarterly'],
                    mode='lines',
                    name='Квартальна сезонність',
                    line=dict(color='orange', width=2)
                ), row=3, col=1)
            
            # Update layout
            fig.update_layout(
                title=f'Компоненти прогнозу - {district}',
                height=800,
                template='plotly_white',
                showlegend=False
            )
            
            if save:
                filename = f"{district.replace(' ', '_').replace('(', '').replace(')', '')}_components.html"
                filepath = os.path.join(self.output_dir, filename)
                fig.write_html(filepath)
                self.logger.info(f"✅ Components plot saved: {filepath}")
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error creating components plot for {district}: {str(e)}")
            return None
    
    def plot_market_overview(self, 
                            forecasts: Dict[str, Dict[str, Any]],
                            save: bool = True) -> Optional[str]:
        """
        Plot market overview across all districts
        
        Args:
            forecasts: Forecast results for all districts
            save: Whether to save the plot
            
        Returns:
            Optional[str]: Path to saved plot file
        """
        try:
            self.logger.info("📊 Creating market overview plot...")
            
            # Prepare data
            districts = []
            price_changes = []
            current_prices = []
            
            for district, forecast_data in forecasts.items():
                if district.startswith('_'):  # Skip meta entries
                    continue
                
                price_change = forecast_data.get('price_change_6m', {})
                if 'percentage_change' in price_change:
                    districts.append(district)
                    price_changes.append(price_change['percentage_change'])
                    current_prices.append(forecast_data.get('current_price', 0))
            
            if not districts:
                self.logger.warning("⚠️ No data available for market overview")
                return None
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Очікувані зміни цін по районах (%)',
                    'Поточні середні ціни по районах (USD)',
                    'Розподіл прогнозованих змін',
                    'Тренди по районах'
                ],
                specs=[[{"type": "bar"}, {"type": "bar"}],
                       [{"type": "histogram"}, {"type": "scatter"}]]
            )
            
            # Price changes by district
            colors = ['red' if x < 0 else 'green' if x > 2 else 'orange' for x in price_changes]
            fig.add_trace(go.Bar(
                x=districts,
                y=price_changes,
                name='Зміна цін (%)',
                marker_color=colors
            ), row=1, col=1)
            
            # Current prices by district
            fig.add_trace(go.Bar(
                x=districts,
                y=current_prices,
                name='Поточна ціна (USD)',
                marker_color='blue'
            ), row=1, col=2)
            
            # Distribution of price changes
            fig.add_trace(go.Histogram(
                x=price_changes,
                nbinsx=10,
                name='Розподіл змін',
                marker_color='purple'
            ), row=2, col=1)
            
            # Scatter plot: current price vs predicted change
            fig.add_trace(go.Scatter(
                x=current_prices,
                y=price_changes,
                mode='markers+text',
                text=districts,
                textposition='top center',
                name='Співвідношення',
                marker=dict(size=10, color='darkblue')
            ), row=2, col=2)
            
            # Update layout
            fig.update_layout(
                title='Огляд ринку нерухомості - Прогноз на 6 місяців',
                height=800,
                template='plotly_white',
                showlegend=False
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Райони", row=1, col=1, tickangle=45)
            fig.update_xaxes(title_text="Райони", row=1, col=2, tickangle=45)
            fig.update_xaxes(title_text="Зміна цін (%)", row=2, col=1)
            fig.update_xaxes(title_text="Поточна ціна (USD)", row=2, col=2)
            
            fig.update_yaxes(title_text="Зміна (%)", row=1, col=1)
            fig.update_yaxes(title_text="Ціна (USD)", row=1, col=2)
            fig.update_yaxes(title_text="Кількість", row=2, col=1)
            fig.update_yaxes(title_text="Зміна (%)", row=2, col=2)
            
            if save:
                filepath = os.path.join(self.output_dir, "market_overview.html")
                fig.write_html(filepath)
                self.logger.info(f"✅ Market overview plot saved: {filepath}")
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error creating market overview plot: {str(e)}")
            return None
    
    def plot_price_distribution(self, 
                               forecasts: Dict[str, Dict[str, Any]],
                               save: bool = True) -> Optional[str]:
        """
        Plot price distribution analysis
        
        Args:
            forecasts: Forecast results for all districts
            save: Whether to save the plot
            
        Returns:
            Optional[str]: Path to saved plot file
        """
        try:
            self.logger.info("📊 Creating price distribution plot...")
            
            # Prepare data
            data_for_plot = []
            
            for district, forecast_data in forecasts.items():
                if district.startswith('_'):
                    continue
                
                future_predictions = forecast_data.get('future_predictions', [])
                for pred in future_predictions:
                    data_for_plot.append({
                        'district': district,
                        'date': pred['date'],
                        'predicted_price': pred['predicted_price'],
                        'lower_bound': pred['lower_bound'],
                        'upper_bound': pred['upper_bound']
                    })
            
            if not data_for_plot:
                return None
            
            df = pd.DataFrame(data_for_plot)
            
            # Create violin plot
            fig = px.violin(
                df, 
                x='district', 
                y='predicted_price',
                title='Розподіл прогнозованих цін по районах',
                labels={'predicted_price': 'Прогнозована ціна (USD)', 'district': 'Район'}
            )
            
            fig.update_layout(
                template='plotly_white',
                height=600,
                xaxis_tickangle=45
            )
            
            if save:
                filepath = os.path.join(self.output_dir, "price_distribution.html")
                fig.write_html(filepath)
                self.logger.info(f"✅ Price distribution plot saved: {filepath}")
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error creating price distribution plot: {str(e)}")
            return None
    
    def create_forecast_report(self, 
                              forecasts: Dict[str, Dict[str, Any]],
                              save: bool = True) -> Optional[str]:
        """
        Create comprehensive forecast report with multiple visualizations
        
        Args:
            forecasts: Forecast results for all districts
            save: Whether to save the report
            
        Returns:
            Optional[str]: Path to saved report file
        """
        try:
            self.logger.info("📊 Creating comprehensive forecast report...")
            
            # Generate individual plots
            plot_paths = []
            
            # Market overview
            overview_path = self.plot_market_overview(forecasts, save=True)
            if overview_path:
                plot_paths.append(overview_path)
            
            # Price distribution
            distribution_path = self.plot_price_distribution(forecasts, save=True)
            if distribution_path:
                plot_paths.append(distribution_path)
            
            # Individual district forecasts (top 5 by activity)
            district_plots = 0
            for district, forecast_data in forecasts.items():
                if district.startswith('_') or district_plots >= 5:
                    continue
                
                # Create sample historical data for plotting
                # In real implementation, this would come from the actual data
                historical_data = pd.DataFrame({
                    'ds': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                    'y': np.random.normal(50000, 5000, 12)  # Sample data
                })
                
                forecast_data_df = pd.DataFrame(forecast_data.get('future_predictions', []))
                if len(forecast_data_df) > 0:
                    forecast_data_df['ds'] = pd.to_datetime(forecast_data_df['date'])
                    forecast_data_df['yhat'] = forecast_data_df['predicted_price']
                    forecast_data_df['yhat_lower'] = forecast_data_df['lower_bound']
                    forecast_data_df['yhat_upper'] = forecast_data_df['upper_bound']
                    
                    district_path = self.plot_district_forecast(
                        district, historical_data, forecast_data_df, save=True
                    )
                    if district_path:
                        plot_paths.append(district_path)
                        district_plots += 1
            
            # Create HTML report combining all plots
            if save and plot_paths:
                report_path = self._create_html_report(forecasts, plot_paths)
                return report_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error creating forecast report: {str(e)}")
            return None
    
    def _create_html_report(self, 
                           forecasts: Dict[str, Dict[str, Any]], 
                           plot_paths: List[str]) -> str:
        """Create HTML report with all visualizations"""
        try:
            report_path = os.path.join(self.output_dir, "forecast_report.html")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Прогноз цін на нерухомість - Івано-Франківськ</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .summary {{ background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .plot-container {{ margin: 30px 0; }}
                    iframe {{ width: 100%; height: 600px; border: none; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Прогноз цін на нерухомість</h1>
                    <h2>Івано-Франківськ - {datetime.now().strftime('%Y-%m-%d')}</h2>
                </div>
                
                <div class="summary">
                    <h3>Підсумок прогнозу</h3>
                    <p>Згенеровано прогнозів для {len([k for k in forecasts.keys() if not k.startswith('_')])} районів</p>
                    <p>Горизонт прогнозування: 6 місяців</p>
                    <p>Дата створення: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
            """
            
            # Add plots
            for plot_path in plot_paths:
                plot_name = os.path.basename(plot_path).replace('.html', '').replace('_', ' ').title()
                html_content += f"""
                <div class="plot-container">
                    <h3>{plot_name}</h3>
                    <iframe src="{os.path.basename(plot_path)}"></iframe>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"✅ Forecast report created: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"❌ Error creating HTML report: {str(e)}")
            return ""


def create_forecast_visualizations(forecasts: Dict[str, Dict[str, Any]], 
                                  output_dir: str = "reports/prophet") -> List[str]:
    """
    Main entry point for creating forecast visualizations
    
    Args:
        forecasts: Forecast results from Prophet
        output_dir: Output directory for plots
        
    Returns:
        List[str]: List of created plot file paths
    """
    plotter = ProphetPlotter(output_dir)
    
    plot_paths = []
    
    # Create market overview
    overview_path = plotter.plot_market_overview(forecasts)
    if overview_path:
        plot_paths.append(overview_path)
    
    # Create price distribution
    distribution_path = plotter.plot_price_distribution(forecasts)
    if distribution_path:
        plot_paths.append(distribution_path)
    
    # Create comprehensive report
    report_path = plotter.create_forecast_report(forecasts)
    if report_path:
        plot_paths.append(report_path)
    
    return plot_paths


if __name__ == "__main__":
    # Test plotting with sample data
    sample_forecasts = {
        'Центр': {
            'current_price': 60000,
            'price_change_6m': {'percentage_change': 5.2},
            'future_predictions': [
                {'date': '2024-03-01', 'predicted_price': 61000, 'lower_bound': 58000, 'upper_bound': 64000},
                {'date': '2024-04-01', 'predicted_price': 62000, 'lower_bound': 59000, 'upper_bound': 65000}
            ]
        },
        'Пасічна': {
            'current_price': 45000,
            'price_change_6m': {'percentage_change': 3.1},
            'future_predictions': [
                {'date': '2024-03-01', 'predicted_price': 46000, 'lower_bound': 43000, 'upper_bound': 49000}
            ]
        }
    }
    
    plotter = ProphetPlotter()
    plot_paths = create_forecast_visualizations(sample_forecasts)
    print(f"Created {len(plot_paths)} visualization files")
