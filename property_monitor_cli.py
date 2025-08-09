#!/usr/bin/env python3
"""
Property Monitor IF - Integrated CLI
===================================

Unified command-line interface for all modules:
- Botasaurus OLX Scraping
- LightAutoML Training & Inference 
- Prophet Time Series Forecasting
- Streamlit Web App Management
- Apache Superset Analytics
"""

import click
import sys
import os
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Setup rich console
console = Console()

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def cli(verbose):
    """🏠 Property Monitor IF - Comprehensive Real Estate Analytics Platform"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    setup_logging()

@cli.group()
def scraper():
    """🤖 Botasaurus OLX Scraper commands"""
    pass

@scraper.command()
@click.option('--mode', type=click.Choice(['sale', 'rent']), default='sale', help='Scraping mode')
@click.option('--pages', default=10, help='Number of pages to scrape')
@click.option('--delay-ms', default=1500, help='Delay between requests (ms)')
@click.option('--headful', is_flag=True, help='Run browser in headful mode')
def scrape(mode, pages, delay_ms, headful):
    """Start OLX scraping session"""
    console.print(f"[blue]🤖 Starting OLX scraping: {mode} mode, {pages} pages[/blue]")
    
    try:
        from scraper import OLXScraper
        
        scraper = OLXScraper()
        result = scraper.scrape_olx({
            'mode': mode,
            'max_pages': pages,
            'delay_ms': delay_ms,
            'headful': headful
        })
        
        if result.success:
            console.print(f"[green]✅ Scraping completed![/green]")
            console.print(f"📊 Processed: {result.total_processed} properties")
            console.print(f"🆕 New: {result.total_new}")
            console.print(f"🔄 Updated: {result.total_updated}")
            console.print(f"❌ Errors: {result.total_errors}")
        else:
            console.print(f"[red]❌ Scraping failed: {result.error_message}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

@scraper.command()
def status():
    """Show scraper statistics"""
    try:
        from scraper.persist import DataPersistence
        
        persistence = DataPersistence()
        stats = persistence.get_statistics()
        
        table = Table(title="Scraper Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Properties", str(stats.get('total_properties', 0)))
        table.add_row("Active Properties", str(stats.get('active_properties', 0)))
        table.add_row("Last Update", stats.get('last_update', 'Never') or 'Never')
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error getting statistics: {str(e)}[/red]")

@cli.group()
def ml():
    """🧠 Machine Learning commands"""
    pass

@ml.command()
@click.option('--timeout', default=300, help='Training timeout in seconds')
@click.option('--cpu-limit', default=4, help='CPU cores limit')
def train(timeout, cpu_limit):
    """Train LightAutoML price prediction model"""
    console.print("[blue]🧠 Training LightAutoML model...[/blue]")
    
    try:
        from ml.laml.train import train_price_model
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Training model...", total=None)
            
            results = train_price_model(
                data_source='sqlite',
                data_path='data/olx_offers.sqlite',
                timeout=timeout,
                cpu_limit=cpu_limit
            )
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✅ Training completed![/green]")
        console.print(f"📊 Validation MAPE: {results['val_metrics']['mape']:.2f}%")
        console.print(f"💰 Validation RMSE: ${results['val_metrics']['rmse']:,.0f}")
        console.print(f"💾 Model saved to: {results['model_path']}")
        
    except Exception as e:
        console.print(f"[red]❌ Training failed: {str(e)}[/red]")
        sys.exit(1)

@ml.command()
@click.argument('input_file')
@click.option('--output', default='prediction_result.json', help='Output file')
def predict(input_file, output):
    """Make price prediction using trained model"""
    try:
        from ml.laml.infer import PricePredictorLAML
        import json
        
        console.print(f"[blue]🔮 Making prediction from {input_file}...[/blue]")
        
        # Load input data
        with open(input_file, 'r', encoding='utf-8') as f:
            property_data = json.load(f)
        
        # Make prediction
        predictor = PricePredictorLAML()
        result = predictor.predict_single(property_data)
        
        # Save result
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Display result
        if 'prediction' in result:
            price = result['prediction']['price_usd']
            confidence = result['prediction']['confidence_interval']
            
            console.print(f"[green]✅ Prediction completed![/green]")
            console.print(f"💰 Estimated price: ${price:,.0f}")
            console.print(f"📊 Confidence: ${confidence['lower']:,.0f} - ${confidence['upper']:,.0f}")
            console.print(f"💾 Saved to: {output}")
        
    except Exception as e:
        console.print(f"[red]❌ Prediction failed: {str(e)}[/red]")
        sys.exit(1)

@ml.command()
def create_sample():
    """Create sample input file for testing"""
    try:
        from ml.laml.utils import create_sample_request
        import json
        
        sample = create_sample_request()
        
        with open('sample_property.json', 'w', encoding='utf-8') as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        
        console.print("[green]✅ Sample property data created: sample_property.json[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

@cli.group()
def forecasting():
    """📈 Prophet Time Series Forecasting commands"""
    pass

@forecasting.command()
@click.option('--min-months', default=6, help='Minimum months of data required')
def prepare(min_months):
    """Prepare time series data for forecasting"""
    console.print("[blue]📊 Preparing time series data...[/blue]")
    
    try:
        from analytics.prophet.prepare_series import prepare_time_series
        
        output_path = prepare_time_series(
            db_path='data/olx_offers.sqlite',
            min_months=min_months
        )
        
        console.print(f"[green]✅ Time series prepared: {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Preparation failed: {str(e)}[/red]")
        sys.exit(1)

@forecasting.command()
@click.option('--horizon', default=6, help='Forecast horizon in months')
def forecast(horizon):
    """Generate Prophet forecasts for districts"""
    console.print(f"[blue]🔮 Creating {horizon}-month forecasts...[/blue]")
    
    try:
        from analytics.prophet.forecast import forecast_districts
        
        output_path = forecast_districts(horizon=horizon)
        
        console.print(f"[green]✅ Forecasts created: {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Forecasting failed: {str(e)}[/red]")
        sys.exit(1)

@forecasting.command()
def plots():
    """Generate forecast visualization plots"""
    console.print("[blue]📊 Creating forecast plots...[/blue]")
    
    try:
        from analytics.prophet.plots import create_forecast_plots
        
        created_plots = create_forecast_plots()
        
        console.print(f"[green]✅ Created {len(created_plots)} plots in reports/prophet/[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Plot creation failed: {str(e)}[/red]")
        sys.exit(1)

@cli.group()
def web():
    """🌐 Web Interface commands"""
    pass

@web.command()
@click.option('--port', default=8501, help='Streamlit port')
@click.option('--host', default='localhost', help='Host address')
def streamlit(port, host):
    """Start Streamlit public interface"""
    console.print(f"[blue]🌐 Starting Streamlit on http://{host}:{port}[/blue]")
    
    try:
        cmd = f"streamlit run app/streamlit_app.py --server.port {port} --server.address {host}"
        subprocess.run(cmd, shell=True)
        
    except KeyboardInterrupt:
        console.print("[yellow]🛑 Streamlit stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start Streamlit: {str(e)}[/red]")

@web.command()
def superset_init():
    """Initialize Apache Superset"""
    console.print("[blue]📊 Initializing Apache Superset...[/blue]")
    
    try:
        from superset.init_superset import main as init_main
        
        result = init_main()
        
        if result == 0:
            console.print("[green]✅ Superset initialized successfully![/green]")
            console.print("🔗 Access: http://localhost:8088 (admin/admin)")
        else:
            console.print("[red]❌ Superset initialization failed[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

@web.command()
@click.option('--port', default=8088, help='Superset port')
def superset(port):
    """Start Apache Superset server"""
    console.print(f"[blue]📊 Starting Superset on http://localhost:{port}[/blue]")
    
    try:
        os.environ['SUPERSET_CONFIG_PATH'] = str(Path('superset/superset_config.py').absolute())
        cmd = f"superset run -h 0.0.0.0 -p {port} --with-threads --reload"
        subprocess.run(cmd, shell=True)
        
    except KeyboardInterrupt:
        console.print("[yellow]🛑 Superset stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start Superset: {str(e)}[/red]")

@cli.command()
def pipeline():
    """🚀 Run complete ML pipeline"""
    console.print(Panel.fit(
        "[bold blue]🚀 Property Monitor IF - Complete Pipeline[/bold blue]\n"
        "Running full end-to-end pipeline:\n"
        "1. Data validation\n"
        "2. ML model training\n" 
        "3. Time series forecasting\n"
        "4. Report generation"
    ))
    
    try:
        # Step 1: Check data
        console.print("\n[blue]📊 Step 1: Validating data...[/blue]")
        from scraper.persist import DataPersistence
        persistence = DataPersistence()
        stats = persistence.get_statistics()
        
        if stats.get('active_properties', 0) < 50:
            console.print("[yellow]⚠️ Warning: Limited data available. Consider running more scraping.[/yellow]")
        
        console.print(f"✅ Found {stats.get('active_properties', 0)} active properties")
        
        # Step 2: Train ML model
        console.print("\n[blue]🧠 Step 2: Training ML model...[/blue]")
        from ml.laml.train import train_price_model
        
        ml_results = train_price_model(
            data_source='sqlite',
            data_path='data/olx_offers.sqlite',
            timeout=300
        )
        
        console.print(f"✅ Model trained - MAPE: {ml_results['val_metrics']['mape']:.2f}%")
        
        # Step 3: Prophet forecasting
        console.print("\n[blue]📈 Step 3: Creating forecasts...[/blue]")
        
        # Prepare time series
        from analytics.prophet.prepare_series import prepare_time_series
        ts_path = prepare_time_series(db_path='data/olx_offers.sqlite')
        console.print(f"✅ Time series prepared: {ts_path}")
        
        # Generate forecasts
        from analytics.prophet.forecast import forecast_districts
        forecast_path = forecast_districts(horizon=6)
        console.print(f"✅ Forecasts created: {forecast_path}")
        
        # Create plots
        from analytics.prophet.plots import create_forecast_plots
        plots = create_forecast_plots()
        console.print(f"✅ Created {len(plots)} forecast plots")
        
        # Step 4: Summary
        console.print("\n[green]🎉 Pipeline completed successfully![/green]")
        
        summary_table = Table(title="Pipeline Results")
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Details", style="magenta")
        
        summary_table.add_row("Data", "✅ Ready", f"{stats.get('active_properties', 0)} properties")
        summary_table.add_row("ML Model", "✅ Trained", f"MAPE: {ml_results['val_metrics']['mape']:.1f}%")
        summary_table.add_row("Forecasts", "✅ Generated", f"{len(plots)} district plots")
        summary_table.add_row("Web Interface", "�� Ready", "Run: property_monitor_cli.py web streamlit")
        summary_table.add_row("Analytics", "🔄 Ready", "Run: property_monitor_cli.py web superset-init")
        
        console.print(summary_table)
        
    except Exception as e:
        console.print(f"[red]❌ Pipeline failed: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
def status():
    """📊 Show system status"""
    console.print("[blue]📊 Property Monitor IF - System Status[/blue]")
    
    status_table = Table(title="System Components Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", style="green")
    status_table.add_column("Details", style="magenta")
    
    # Check database
    try:
        from scraper.persist import DataPersistence
        persistence = DataPersistence()
        stats = persistence.get_statistics()
        status_table.add_row("Database", "✅ Active", f"{stats.get('active_properties', 0)} properties")
    except:
        status_table.add_row("Database", "❌ Error", "No data or connection issue")
    
    # Check ML model
    model_path = Path('models/laml_price.bin')
    if model_path.exists():
        status_table.add_row("ML Model", "✅ Available", f"Trained model ready")
    else:
        status_table.add_row("ML Model", "⚠️ Missing", "Run: ml train")
    
    # Check forecasts
    forecast_path = Path('analytics/district_forecasts.csv')
    if forecast_path.exists():
        status_table.add_row("Forecasts", "✅ Available", "Prophet forecasts ready")
    else:
        status_table.add_row("Forecasts", "⚠️ Missing", "Run: forecasting forecast")
    
    # Check reports
    reports_dir = Path('reports')
    if reports_dir.exists() and any(reports_dir.iterdir()):
        status_table.add_row("Reports", "✅ Generated", "Analysis reports available")
    else:
        status_table.add_row("Reports", "⚠️ Missing", "Run: pipeline")
    
    console.print(status_table)
    
    # Quick start suggestions
    console.print("\n[bold]🚀 Quick Start Commands:[/bold]")
    console.print("1. [cyan]property_monitor_cli.py scraper scrape --mode sale --pages 5[/cyan] - Get data")
    console.print("2. [cyan]property_monitor_cli.py pipeline[/cyan] - Run full ML pipeline") 
    console.print("3. [cyan]property_monitor_cli.py web streamlit[/cyan] - Start public interface")
    console.print("4. [cyan]property_monitor_cli.py web superset-init && property_monitor_cli.py web superset[/cyan] - Start analytics")

@cli.command()
def install():
    """📦 Install and setup all dependencies"""
    console.print("[blue]📦 Installing Property Monitor IF dependencies...[/blue]")
    
    try:
        # Install Python packages
        console.print("Installing Python packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # Install Playwright
        console.print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        
        # Create directories
        console.print("Creating directories...")
        for dir_path in ['data/exports', 'models', 'reports/prophet', 'scraper/logs']:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        console.print("[green]✅ Installation completed![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. [cyan]property_monitor_cli.py status[/cyan] - Check system status")
        console.print("2. [cyan]property_monitor_cli.py scraper scrape[/cyan] - Start collecting data")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Installation failed: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    cli()
