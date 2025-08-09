# 🔥 Glow Nest XGB - 5-Module ML System Integration

## 🎯 System Overview

This project has been successfully integrated with a comprehensive 5-module machine learning system for real estate price prediction and analytics in Ivano-Frankivsk:

### Module Architecture

```
Glow Nest XGB ML System
├── Module 1: Botasaurus OLX Scraper      (scraper/)
├── Module 2: LightAutoML Price Prediction (ml/laml/)  
├── Module 3: Prophet Time Series Forecasting (analytics/prophet/)
├── Module 4: Streamlit Public Interface   (app/)
└── Module 5: Apache Superset Analytics   (superset/)
```

## 🚀 Quick Start

### 1. Setup (First Time Only)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize system
python setup_ml_system.py

# Check system status
python property_monitor_cli.py status
```

### 2. Data Collection
```bash
# Start Botasaurus scraper (anti-detection enabled)
python property_monitor_cli.py scraper start

# Monitor progress
python property_monitor_cli.py scraper status
```

### 3. Model Training
```bash
# Train LightAutoML model (MAPE target: ≤15%)
python property_monitor_cli.py ml train

# Check model performance
python property_monitor_cli.py ml status
```

### 4. Forecasting
```bash
# Generate 6-month Prophet forecasts for all districts
python property_monitor_cli.py forecasting predict --all

# Generate forecast for specific district
python property_monitor_cli.py forecasting predict --district "Центр"
```

### 5. Web Interfaces
```bash
# Start Streamlit public interface (port 8501)
python property_monitor_cli.py web start

# Start Apache Superset analytics (port 8088)  
python property_monitor_cli.py superset start
```

## 📊 Module Details

### Module 1: Botasaurus OLX Scraper
- **Purpose**: Anti-detection web scraping from OLX.ua
- **Features**: 
  - Stealth mode with user-agent rotation
  - Resume capability for interrupted scraping
  - Street-to-district mapping for 57+ streets in Ivano-Frankivsk
  - Seller classification (owner vs agency)
  - Price change detection
- **Location**: `scraper/`
- **CLI**: `python property_monitor_cli.py scraper [start|stop|status]`

### Module 2: LightAutoML Price Prediction
- **Purpose**: Automated machine learning for price prediction
- **Target**: MAPE ≤ 15% accuracy
- **Features**:
  - Automated feature engineering
  - Model selection and hyperparameter tuning
  - Feature importance analysis
  - Real-time inference API
- **Location**: `ml/laml/`
- **CLI**: `python property_monitor_cli.py ml [train|infer|status]`

### Module 3: Prophet Time Series Forecasting
- **Purpose**: 6-month price trend forecasting by districts
- **Features**:
  - Facebook Prophet integration
  - Confidence intervals
  - Seasonal decomposition
  - District-level analysis
  - Visualization generation
- **Location**: `analytics/prophet/`
- **CLI**: `python property_monitor_cli.py forecasting [predict|plot]`

### Module 4: Streamlit Public Interface
- **Purpose**: Mobile-responsive web interface for property evaluation
- **Features**:
  - Real-time ML predictions (≤1.5 second response)
  - Similar property recommendations
  - Feature importance visualization
  - Price history charts
  - Mobile-optimized design
- **Location**: `app/`
- **URL**: `http://localhost:8501`
- **CLI**: `python property_monitor_cli.py web [start|stop|status]`

### Module 5: Apache Superset Analytics
- **Purpose**: Business intelligence dashboards
- **Features**:
  - 4 Pre-configured dashboards:
    - Market Overview IF
    - Dynamics & Trends  
    - Model Quality
    - Scraper Health
  - Interactive charts and filters
  - SQLite integration
- **Location**: `superset/`
- **URL**: `http://localhost:8088`
- **CLI**: `python property_monitor_cli.py superset [start|stop|init]`

## 🛠️ API Integration

### New Express.js Endpoints

The existing Express.js server has been enhanced with ML integration endpoints:

```typescript
// ML Prediction
POST /api/ml/predict
{
  "area": 65,
  "district": "Центр", 
  "rooms": 2,
  "floor": 3,
  "building_type": "apartment",
  "renovation": "good"
}

// Prophet Forecasting
GET /api/ml/forecast?district=Центр

// Model Training
POST /api/ml/train

// Streamlit Control
POST /api/streamlit/start
POST /api/streamlit/stop
GET /api/streamlit/status

// Superset Status
GET /api/superset/status

// Pipeline Status
GET /api/pipeline/status
```

## 🎛️ Admin Panel Integration

The admin panel (`/admin`) now includes a new "ML Модулі (5 систем)" section with:

- **System Overview**: Visual status of all 5 modules
- **LightAutoML Controls**: Model training and status
- **Prophet Forecasting**: Trend generation for districts
- **Streamlit Management**: Start/stop web interface
- **Superset Analytics**: Dashboard access
- **Unified CLI Commands**: Documentation and quick actions

## 📁 Directory Structure

```
project/
├── scraper/                    # Module 1: Botasaurus
│   ├── olx_scraper.py         # Main scraper with anti-detection
│   ├── parsing.py             # HTML parsing and data extraction
│   ├── classify.py            # Seller classification logic
│   ├── config.py              # Scraper configuration
│   └── logs/                  # Scraping logs
├── ml/laml/                   # Module 2: LightAutoML
│   ├── train.py               # Model training pipeline
│   ├── infer.py               # Real-time inference
│   ├── features.py            # Feature engineering
│   └── models/                # Trained model artifacts
├── analytics/prophet/         # Module 3: Prophet Forecasting
│   ├── forecast.py            # Time series forecasting
│   ├── prepare_series.py      # Data preparation
│   └── plots.py               # Visualization generation
├── app/                       # Module 4: Streamlit Interface
│   └── streamlit_app.py       # Mobile-responsive web app
├── superset/                  # Module 5: Apache Superset
│   ├── superset_config.py     # Superset configuration
│   └── init_superset.py       # Dashboard initialization
├── data/                      # Shared data storage
│   └── exports/               # Export directory
├── models/                    # Model artifacts
├── reports/                   # Generated reports
│   └── prophet/               # Prophet plots and forecasts
├── property_monitor_cli.py    # Unified CLI interface
├── setup_ml_system.py         # System setup script
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom ports
STREAMLIT_PORT=8501
SUPERSET_PORT=8088

# Optional: Set model parameters
ML_TARGET_MAPE=15
PROPHET_PERIODS=180  # 6 months
```

### CLI Configuration
The unified CLI supports rich console output and progress tracking:
```bash
python property_monitor_cli.py --help  # Show all commands
python property_monitor_cli.py scraper --help  # Module-specific help
```

## 📈 Performance Targets

- **Scraping**: 4-8 second delays between requests (anti-ban)
- **ML Training**: MAPE ≤ 15% on test set
- **Inference**: ≤ 1.5 seconds response time
- **Forecasting**: 6-month predictions with confidence intervals
- **Web Interface**: Mobile-responsive, ≤ 3 second load time

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **Database Errors**: Run `python setup_ml_system.py`
3. **Permission Errors**: Check file permissions on data/ and models/
4. **Port Conflicts**: Modify ports in CLI config or environment variables

### Debug Commands
```bash
python property_monitor_cli.py status        # Check all modules
python property_monitor_cli.py scraper logs  # View scraper logs
python property_monitor_cli.py ml validate   # Validate ML pipeline
```

## 🔄 Complete Pipeline Example

```bash
# 1. Initialize system
python setup_ml_system.py

# 2. Collect data (10-15 minutes)
python property_monitor_cli.py scraper start

# 3. Train ML model (5-10 minutes)  
python property_monitor_cli.py ml train

# 4. Generate forecasts (2-3 minutes)
python property_monitor_cli.py forecasting predict --all

# 5. Start web interfaces
python property_monitor_cli.py web start
python property_monitor_cli.py superset start

# 6. Run full pipeline (automated)
python property_monitor_cli.py pipeline full
```

## 📝 NPM Scripts

For convenience, the following npm scripts are available:

```json
{
  "ml:cli": "python property_monitor_cli.py",
  "ml:train": "python property_monitor_cli.py ml train", 
  "ml:forecast": "python property_monitor_cli.py forecasting predict --all",
  "ml:streamlit": "python property_monitor_cli.py web start",
  "ml:superset": "python property_monitor_cli.py superset start",
  "ml:pipeline": "python property_monitor_cli.py pipeline full",
  "ml:status": "python property_monitor_cli.py status"
}
```

Usage: `npm run ml:train` or `npm run ml:status`

## 🎉 Success Criteria

✅ **Integration Complete**: All 5 modules integrated with existing React/TypeScript frontend  
✅ **API Endpoints**: New ML endpoints added to Express.js server  
✅ **Admin Panel**: Enhanced with ML controls and monitoring  
✅ **Unified CLI**: Single interface for all 5 modules  
✅ **Database**: Shared SQLite schema across all modules  
✅ **Mobile-Responsive**: Streamlit interface optimized for mobile  
✅ **Anti-Detection**: Botasaurus scraper with stealth capabilities  
✅ **Production-Ready**: Error handling, logging, and monitoring

The system is now ready for production use with comprehensive real estate analytics capabilities!
