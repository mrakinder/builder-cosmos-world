#!/usr/bin/env python3
"""
Setup script for the 5-module ML system:
1. Botasaurus OLX Scraper
2. LightAutoML Price Prediction  
3. Prophet Time Series Forecasting
4. Streamlit Public Interface
5. Apache Superset Analytics

This script prepares the system for production use.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Ensure Python 3.8+ is being used"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install all required Python packages"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run manually: pip install -r requirements.txt")
        return False

def setup_database():
    """Initialize the SQLite database with proper schema"""
    print("\n🗄️  Setting up database...")
    
    db_path = "glow_nest.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create properties table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                olx_id TEXT UNIQUE,
                title TEXT,
                price_usd REAL,
                area REAL,
                floor INTEGER,
                district TEXT,
                description TEXT,
                url TEXT,
                isOwner BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create street_district_map table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS street_district_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street TEXT UNIQUE,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create activity_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                module TEXT,
                action TEXT,
                details TEXT,
                status TEXT
            )
        """)
        
        # Create model_metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                metric_name TEXT,
                metric_value REAL,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database schema initialized")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_directories():
    """Create necessary directories for the system"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "data/exports",
        "models", 
        "reports/prophet",
        "scraper/logs",
        "ml/laml/models",
        "analytics/prophet/plots"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created")

def test_system_components():
    """Test that all 5 modules can be imported"""
    print("\n🔧 Testing system components...")
    
    tests = [
        ("Botasaurus Scraper", "scraper.olx_scraper"),
        ("LightAutoML", "ml.laml.train"),
        ("Prophet Forecasting", "analytics.prophet.forecast"),
        ("Streamlit App", "app.streamlit_app"),
        ("CLI Interface", "property_monitor_cli")
    ]
    
    all_passed = True
    for name, module in tests:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: Failed - {e}")
            all_passed = False
    
    return all_passed

def show_usage_instructions():
    """Display usage instructions for the integrated system"""
    print("\n" + "="*60)
    print("🎉 GLOW NEST XGB 5-MODULE SYSTEM READY!")
    print("="*60)
    print()
    print("📋 Available Commands:")
    print("   python property_monitor_cli.py status           # System status")
    print("   python property_monitor_cli.py scraper start    # Start Botasaurus scraper")
    print("   python property_monitor_cli.py ml train         # Train LightAutoML model")
    print("   python property_monitor_cli.py forecasting predict --all  # Prophet forecasts")
    print("   python property_monitor_cli.py web start        # Launch Streamlit interface") 
    print("   python property_monitor_cli.py superset start   # Start Superset analytics")
    print("   python property_monitor_cli.py pipeline full    # Run complete pipeline")
    print()
    print("📊 NPM Scripts:")
    print("   npm run ml:train      # Quick ML training")
    print("   npm run ml:forecast   # Generate forecasts")
    print("   npm run ml:streamlit  # Start web interface")
    print("   npm run ml:status     # Check system status")
    print()
    print("🌐 Web Interfaces:")
    print("   Admin Panel:    /admin")
    print("   Statistics:     /statistics") 
    print("   Streamlit:      http://localhost:8501 (after ml:streamlit)")
    print("   Superset:       http://localhost:8088 (after superset start)")
    print()
    print("📁 Directory Structure:")
    print("   scraper/       - Botasaurus web scraping")
    print("   ml/laml/       - LightAutoML models")
    print("   analytics/     - Prophet time series")
    print("   app/           - Streamlit web interface")
    print("   superset/      - Apache Superset configs")
    print("   data/          - Shared data storage")
    print("   models/        - Trained model artifacts")
    print("   reports/       - Generated reports and plots")
    print()
    print("🚀 Next Steps:")
    print("   1. Run: python property_monitor_cli.py scraper start")
    print("   2. Wait for data collection (10-15 minutes)")
    print("   3. Run: python property_monitor_cli.py ml train")
    print("   4. Run: python property_monitor_cli.py web start")
    print("   5. Access Streamlit at http://localhost:8501")
    print()

def main():
    """Main setup function"""
    print("🔥 GLOW NEST XGB - 5-Module ML System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Dependencies installation failed. Please install manually:")
        print("   pip install -r requirements.txt")
    
    # Setup database
    if not setup_database():
        return False
    
    # Create directories
    create_directories()
    
    # Test components
    if not test_system_components():
        print("\n⚠️  Some components failed to load. Check dependencies.")
    
    # Show usage
    show_usage_instructions()
    
    print("✅ Setup completed successfully!")
    return True

if __name__ == "__main__":
    main()
