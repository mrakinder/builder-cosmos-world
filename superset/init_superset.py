"""
Apache Superset Initialization Script
====================================

Sets up Superset with predefined dashboards and datasets for Property Monitor IF.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def setup_superset_database():
    """Initialize Superset database and create admin user"""
    print("🔧 Initializing Superset database...")
    
    # Set environment variables
    os.environ['SUPERSET_CONFIG_PATH'] = str(Path('superset/superset_config.py').absolute())
    
    # Initialize Superset
    os.system('superset db upgrade')
    os.system('superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin')
    os.system('superset init')
    
    print("✅ Superset database initialized")

def create_datasets_config():
    """Create configuration for Superset datasets"""
    
    datasets_config = {
        "offers_active": {
            "table_name": "offers_active_view", 
            "sql": """
                SELECT 
                    ad_id,
                    title,
                    price_value as price_usd,
                    area_total,
                    rooms,
                    floor,
                    floors_total,
                    district,
                    street,
                    building_type,
                    renovation,
                    seller_type,
                    CAST(strftime('%Y', scraped_at) AS INTEGER) as year,
                    CAST(strftime('%m', scraped_at) AS INTEGER) as month,
                    DATE(scraped_at) as scraped_date,
                    ROUND(price_value / area_total, 2) as price_per_sqm,
                    CASE 
                        WHEN floor = 1 THEN 'Перший поверх'
                        WHEN floor = floors_total THEN 'Останній поверх'
                        ELSE 'Середні поверхи'
                    END as floor_category,
                    CASE
                        WHEN price_value < 30000 THEN 'До $30k'
                        WHEN price_value < 60000 THEN '$30k-60k'
                        WHEN price_value < 100000 THEN '$60k-100k'
                        ELSE 'Понад $100k'
                    END as price_range
                FROM offers 
                WHERE is_active = 1 
                  AND price_value IS NOT NULL 
                  AND price_currency = 'USD'
            """,
            "description": "Active property offers with calculated metrics"
        },
        
        "offers_all": {
            "table_name": "offers_all_view",
            "sql": """
                SELECT 
                    ad_id,
                    title,
                    price_value as price_usd,
                    area_total,
                    rooms,
                    district,
                    seller_type,
                    is_active,
                    DATE(scraped_at) as scraped_date,
                    DATE(first_seen_at) as first_seen_date,
                    DATE(last_seen_at) as last_seen_date,
                    ROUND(price_value / area_total, 2) as price_per_sqm
                FROM offers 
                WHERE price_value IS NOT NULL 
                  AND price_currency = 'USD'
            """,
            "description": "All property offers including inactive"
        },
        
        "district_summary": {
            "table_name": "district_summary_view",
            "sql": """
                SELECT 
                    district,
                    COUNT(*) as total_offers,
                    AVG(price_value) as avg_price,
                    MEDIAN(price_value) as median_price,
                    AVG(area_total) as avg_area,
                    AVG(price_value / area_total) as avg_price_per_sqm,
                    MIN(price_value) as min_price,
                    MAX(price_value) as max_price,
                    COUNT(CASE WHEN seller_type = 'owner' THEN 1 END) as owner_offers,
                    COUNT(CASE WHEN seller_type = 'agency' THEN 1 END) as agency_offers
                FROM offers 
                WHERE is_active = 1 
                  AND price_value IS NOT NULL 
                  AND price_currency = 'USD'
                  AND district IS NOT NULL
                GROUP BY district
            """,
            "description": "Summary statistics by district"
        }
    }
    
    return datasets_config

def create_dashboard_configs():
    """Create configuration for Superset dashboards"""
    
    dashboards_config = {
        "market_overview_if": {
            "title": "Market Overview IF",
            "description": "Real estate market overview for Ivano-Frankivsk",
            "charts": [
                {
                    "title": "Price Distribution by District",
                    "chart_type": "bar",
                    "dataset": "district_summary",
                    "metrics": ["avg_price"],
                    "groupby": ["district"]
                },
                {
                    "title": "Properties by Price Range",
                    "chart_type": "pie",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(*)"],
                    "groupby": ["price_range"]
                },
                {
                    "title": "Average Price per m² by District",
                    "chart_type": "bar",
                    "dataset": "district_summary", 
                    "metrics": ["avg_price_per_sqm"],
                    "groupby": ["district"]
                },
                {
                    "title": "Owner vs Agency Distribution",
                    "chart_type": "pie",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(*)"],
                    "groupby": ["seller_type"]
                }
            ]
        },
        
        "dynamics_trends": {
            "title": "Dynamics & Trends",
            "description": "Time series analysis and price trends",
            "charts": [
                {
                    "title": "Monthly Price Trends",
                    "chart_type": "line",
                    "dataset": "offers_active",
                    "metrics": ["AVG(price_usd)"],
                    "groupby": ["scraped_date"]
                },
                {
                    "title": "New Listings Over Time",
                    "chart_type": "area",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(*)"],
                    "groupby": ["scraped_date"]
                },
                {
                    "title": "Price Volatility by District",
                    "chart_type": "box_plot",
                    "dataset": "offers_active",
                    "metrics": ["price_usd"],
                    "groupby": ["district"]
                }
            ]
        },
        
        "model_quality": {
            "title": "Model Quality",
            "description": "ML model performance and feature importance",
            "charts": [
                {
                    "title": "Model Metrics Over Time",
                    "chart_type": "line",
                    "dataset": "model_metrics",
                    "metrics": ["mape", "rmse"],
                    "groupby": ["training_date"]
                },
                {
                    "title": "Feature Importance",
                    "chart_type": "bar",
                    "dataset": "feature_importance",
                    "metrics": ["importance"],
                    "groupby": ["feature"]
                }
            ]
        },
        
        "scraper_health": {
            "title": "Scraper Health",
            "description": "Scraping system monitoring and health",
            "charts": [
                {
                    "title": "Daily Scraping Volume",
                    "chart_type": "bar",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(*)"],
                    "groupby": ["scraped_date"]
                },
                {
                    "title": "Data Quality Score",
                    "chart_type": "gauge",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(CASE WHEN price_usd IS NOT NULL THEN 1 END) / COUNT(*) * 100"]
                },
                {
                    "title": "Properties by Source",
                    "chart_type": "pie",
                    "dataset": "offers_active",
                    "metrics": ["COUNT(*)"],
                    "groupby": ["seller_type"]
                }
            ]
        }
    }
    
    return dashboards_config

def save_configurations():
    """Save dataset and dashboard configurations to files"""
    
    config_dir = Path('superset/configs')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Save datasets config
    datasets_config = create_datasets_config()
    with open(config_dir / 'datasets.json', 'w', encoding='utf-8') as f:
        json.dump(datasets_config, f, indent=2, ensure_ascii=False)
    
    # Save dashboards config
    dashboards_config = create_dashboard_configs()
    with open(config_dir / 'dashboards.json', 'w', encoding='utf-8') as f:
        json.dump(dashboards_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configurations saved to superset/configs/")
    
    return datasets_config, dashboards_config

def create_sample_data():
    """Create sample data for testing if no real data exists"""
    
    db_path = Path('data/olx_offers.sqlite')
    
    # Check if database exists and has data
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            count = pd.read_sql("SELECT COUNT(*) as count FROM offers WHERE is_active = 1", conn)
            if count.iloc[0]['count'] > 0:
                print("✅ Real data found in database")
                return
    
    print("⚠️ No real data found. Creating sample data for Superset demo...")
    
    # Create sample data
    sample_data = []
    districts = ["Центр", "Пасічна", "БАМ", "Каскад", "Брати"]
    
    for i in range(100):
        district = districts[i % len(districts)]
        base_price = {"Центр": 70000, "Пасічна": 55000, "БАМ": 45000, "Каскад": 60000, "Брати": 40000}[district]
        
        area = 45 + (i % 60)  # 45-105 m²
        price = base_price + (area - 60) * 800 + (i % 20000 - 10000)  # Add variation
        
        sample_data.append({
            'ad_id': f'sample_{i}',
            'title': f'Sample Property {i}',
            'price_value': price,
            'price_currency': 'USD',
            'area_total': area,
            'rooms': (i % 4) + 1,
            'floor': (i % 9) + 1,
            'floors_total': 9,
            'district': district,
            'street': f'Sample Street {i % 10}',
            'building_type': ['панель', 'цегла', 'монолітно-цегляний'][i % 3],
            'renovation': ['косметичний', 'євроремонт', 'під ремонт'][i % 3],
            'seller_type': ['owner', 'agency'][i % 2],
            'is_active': 1,
            'scraped_at': f'2024-01-{(i % 28) + 1:02d} 12:00:00',
            'first_seen_at': f'2024-01-{(i % 28) + 1:02d} 12:00:00',
            'last_seen_at': f'2024-01-{(i % 28) + 1:02d} 12:00:00'
        })
    
    # Save to database
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        # Create table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                ad_id TEXT PRIMARY KEY,
                title TEXT,
                price_value REAL,
                price_currency TEXT,
                area_total REAL,
                rooms INTEGER,
                floor INTEGER,
                floors_total INTEGER,
                district TEXT,
                street TEXT,
                building_type TEXT,
                renovation TEXT,
                seller_type TEXT,
                is_active BOOLEAN,
                scraped_at TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT
            )
        """)
        
        # Insert sample data
        df = pd.DataFrame(sample_data)
        df.to_sql('offers', conn, if_exists='replace', index=False)
    
    print("✅ Sample data created")

def main():
    """Main initialization function"""
    print("🚀 Initializing Apache Superset for Property Monitor IF")
    print("=" * 60)
    
    try:
        # Create sample data if needed
        create_sample_data()
        
        # Save configurations
        datasets_config, dashboards_config = save_configurations()
        
        # Setup Superset
        setup_superset_database()
        
        print("\n✅ Superset initialization completed!")
        print("\n📊 Next steps:")
        print("1. Start Superset: superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger")
        print("2. Login: http://localhost:8088 (admin/admin)")
        print("3. Import datasets and dashboards using the configs in superset/configs/")
        print("\n📁 Available dashboards:")
        for dashboard_id, config in dashboards_config.items():
            print(f"   - {config['title']}: {config['description']}")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
