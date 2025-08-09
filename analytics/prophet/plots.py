"""
Prophet plotting and visualization module
========================================

Creates charts and visualizations for Prophet forecasts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Set matplotlib backend for server environments
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

class ForecastPlotter:
    """Creates plots for Prophet forecasting results"""
    
    def __init__(self, output_dir: str = 'reports/prophet'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set plot style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configure matplotlib for Ukrainian text
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_district_forecast(
        self, 
        forecast_data: pd.DataFrame, 
        district: str,
        segment: str = 'all',
        save_path: Optional[str] = None
    ) -> str:
        """
        Create forecast plot for a specific district
        
        Args:
            forecast_data: Forecast DataFrame
            district: District name
            segment: Segment name
            save_path: Custom save path
            
        Returns:
            Path to saved plot
        """
        # Filter data for this district-segment
        series_name = f"{district}_{segment}" if segment != 'all' else district
        plot_data = forecast_data[forecast_data['series_name'] == series_name].copy()
        
        if len(plot_data) == 0:
            logger.warning(f"No data found for {series_name}")
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Split historical and forecast data
        historical = plot_data[plot_data['is_forecast'] == False].copy()
        future = plot_data[plot_data['is_forecast'] == True].copy()
        
        # Plot historical data
        if len(historical) > 0:
            ax.plot(historical['ds'], historical['yhat'], 
                   color='blue', linewidth=2, label='Історичні дані')
            
            # Historical confidence interval
            ax.fill_between(historical['ds'], 
                          historical['yhat_lower'], 
                          historical['yhat_upper'],
                          alpha=0.2, color='blue')
        
        # Plot forecast
        if len(future) > 0:
            ax.plot(future['ds'], future['yhat'], 
                   color='red', linewidth=2, linestyle='--', 
                   label='Прогноз')
            
            # Forecast confidence interval
            ax.fill_between(future['ds'], 
                          future['yhat_lower'], 
                          future['yhat_upper'],
                          alpha=0.3, color='red', label='Довірчий інтервал')
        
        # Formatting
        ax.set_title(f'Прогноз цін нерухомості: {district}\n({segment})', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Ціна, USD', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            filename = f"forecast_{district}_{segment}.png".replace(' ', '_').replace('(', '').replace(')', '')
            save_path = self.output_dir / filename
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved forecast plot: {save_path}")
        return str(save_path)
    
    def plot_all_districts_overview(
        self, 
        forecast_data: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create overview plot with all districts
        
        Args:
            forecast_data: Complete forecast DataFrame
            save_path: Custom save path
            
        Returns:
            Path to saved plot
        """
        # Get unique districts
        districts = forecast_data['district'].unique()
        
        # Create subplots
        n_districts = len(districts)
        n_cols = min(3, n_districts)
        n_rows = (n_districts + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
        if n_districts == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes
        else:
            axes = axes.flatten()
        
        for i, district in enumerate(districts):
            if i >= len(axes):
                break
                
            ax = axes[i]
            
            # Get data for this district (all segments combined)
            district_data = forecast_data[forecast_data['district'] == district].copy()
            
            # Group by date and average across segments
            daily_avg = district_data.groupby(['ds', 'is_forecast']).agg({
                'yhat': 'mean',
                'yhat_lower': 'mean',
                'yhat_upper': 'mean'
            }).reset_index()
            
            # Split historical and forecast
            historical = daily_avg[daily_avg['is_forecast'] == False]
            future = daily_avg[daily_avg['is_forecast'] == True]
            
            # Plot
            if len(historical) > 0:
                ax.plot(historical['ds'], historical['yhat'], 
                       color='blue', linewidth=2)
                ax.fill_between(historical['ds'], 
                              historical['yhat_lower'], 
                              historical['yhat_upper'],
                              alpha=0.2, color='blue')
            
            if len(future) > 0:
                ax.plot(future['ds'], future['yhat'], 
                       color='red', linewidth=2, linestyle='--')
                ax.fill_between(future['ds'], 
                              future['yhat_lower'], 
                              future['yhat_upper'],
                              alpha=0.3, color='red')
            
            ax.set_title(district, fontsize=12)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}k'))
            ax.grid(True, alpha=0.3)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Hide empty subplots
        for i in range(n_districts, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle('Огляд прогнозів по всіх районах', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            save_path = self.output_dir / "all_districts_overview.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved overview plot: {save_path}")
        return str(save_path)
    
    def plot_price_changes_summary(
        self, 
        summary_data: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> str:
        """
        Create summary plot of price changes by district
        
        Args:
            summary_data: Forecast summary data
            save_path: Custom save path
            
        Returns:
            Path to saved plot
        """
        # Extract price change data
        series_summary = summary_data.get('series_summary', {})
        
        if not series_summary:
            logger.warning("No series summary data available for plotting")
            return None
        
        # Prepare data for plotting
        plot_data = []
        for series_name, data in series_summary.items():
            plot_data.append({
                'district': data['district'],
                'segment': data['segment'],
                'price_change_pct': data['price_change_pct'],
                'trend': data['trend'],
                'current_price': data['current_price'],
                'forecast_price': data['forecast_price']
            })
        
        df = pd.DataFrame(plot_data)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Price change by district
        district_changes = df.groupby('district')['price_change_pct'].mean().sort_values()
        
        colors = ['red' if x < 0 else 'green' if x > 2 else 'gray' for x in district_changes.values]
        
        bars1 = ax1.barh(range(len(district_changes)), district_changes.values, color=colors)
        ax1.set_yticks(range(len(district_changes)))
        ax1.set_yticklabels(district_changes.index)
        ax1.set_xlabel('Зміна ціни, %')
        ax1.set_title('Прогнозована зміна цін по районах\n(6 місяців)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(0, color='black', linestyle='-', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars1, district_changes.values)):
            ax1.text(value + (1 if value >= 0 else -1), i, f'{value:.1f}%', 
                    va='center', ha='left' if value >= 0 else 'right')
        
        # Plot 2: Current vs forecast prices
        ax2.scatter(df['current_price'], df['forecast_price'], 
                   c=df['price_change_pct'], cmap='RdYlGn', s=100, alpha=0.7)
        
        # Add diagonal line
        min_price = min(df['current_price'].min(), df['forecast_price'].min())
        max_price = max(df['current_price'].max(), df['forecast_price'].max())
        ax2.plot([min_price, max_price], [min_price, max_price], 
                'k--', alpha=0.5, label='Без змін')
        
        ax2.set_xlabel('Поточна ціна, USD')
        ax2.set_ylabel('Прогнозована ціна, USD')
        ax2.set_title('Поточні vs прогнозовані ціни', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Format axis as currency
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}k'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}k'))
        
        # Add colorbar
        cbar = plt.colorbar(ax2.collections[0], ax=ax2)
        cbar.set_label('Зміна ціни, %')
        
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            save_path = self.output_dir / "price_changes_summary.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved price changes summary: {save_path}")
        return str(save_path)

def create_forecast_plots(
    forecast_path: str = 'analytics/district_forecasts.csv',
    summary_path: str = 'analytics/forecast_summary.json',
    output_dir: str = 'reports/prophet'
) -> List[str]:
    """
    Create all forecast plots
    
    Args:
        forecast_path: Path to forecast CSV
        summary_path: Path to summary JSON
        output_dir: Output directory for plots
        
    Returns:
        List of paths to created plots
    """
    logger.info("Creating forecast plots")
    
    try:
        # Load data
        forecast_df = pd.read_csv(forecast_path)
        forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Initialize plotter
        plotter = ForecastPlotter(output_dir)
        
        created_plots = []
        
        # Create individual district plots
        for series_name in forecast_df['series_name'].unique():
            district = series_name.split('_')[0]
            segment = '_'.join(series_name.split('_')[1:]) if '_' in series_name else 'all'
            
            try:
                plot_path = plotter.plot_district_forecast(
                    forecast_df, district, segment
                )
                if plot_path:
                    created_plots.append(plot_path)
            except Exception as e:
                logger.error(f"Failed to create plot for {series_name}: {str(e)}")
        
        # Create overview plot
        try:
            overview_path = plotter.plot_all_districts_overview(forecast_df)
            if overview_path:
                created_plots.append(overview_path)
        except Exception as e:
            logger.error(f"Failed to create overview plot: {str(e)}")
        
        # Create price changes summary
        try:
            summary_plot_path = plotter.plot_price_changes_summary(summary_data)
            if summary_plot_path:
                created_plots.append(summary_plot_path)
        except Exception as e:
            logger.error(f"Failed to create summary plot: {str(e)}")
        
        logger.info(f"Created {len(created_plots)} forecast plots")
        return created_plots
        
    except Exception as e:
        logger.error(f"Plot creation failed: {str(e)}")
        raise

def main():
    """CLI interface for plot creation"""
    parser = argparse.ArgumentParser(description='Create Prophet forecast plots')
    parser.add_argument('--forecast', default='analytics/district_forecasts.csv',
                       help='Forecast CSV file path')
    parser.add_argument('--summary', default='analytics/forecast_summary.json',
                       help='Summary JSON file path')
    parser.add_argument('--output-dir', default='reports/prophet',
                       help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        created_plots = create_forecast_plots(
            forecast_path=args.forecast,
            summary_path=args.summary,
            output_dir=args.output_dir
        )
        
        print(f"\n✅ Plot creation completed!")
        print(f"Created {len(created_plots)} plots in: {args.output_dir}")
        
    except Exception as e:
        print(f"\n❌ Plot creation failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
