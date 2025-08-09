"""
Apache Superset Configuration for Property Monitor IF
===================================================

Configuration file for Superset analytics dashboard.
"""

import os
from pathlib import Path

# Database Configuration
SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path('data/olx_offers.sqlite').absolute()}"

# Security Configuration
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your-secret-key-change-in-production')

# Basic Configuration
SUPERSET_WEBSERVER_PORT = 8088
SUPERSET_WEBSERVER_ADDRESS = '0.0.0.0'

# Feature Flags
FEATURE_FLAGS = {
    'DASHBOARD_NATIVE_FILTERS': True,
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'ESCAPE_MARKDOWN_HTML': False,
}

# Cache Configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# CSV Export Configuration
CSV_EXPORT = {
    'encoding': 'utf-8'
}

# Email Configuration (optional)
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = os.environ.get('SMTP_USER', 'superset')
SMTP_PORT = 587
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_MAIL_FROM = os.environ.get('SMTP_MAIL_FROM', 'superset@localhost')

# Security Configuration
ENABLE_PROXY_FIX = True
PUBLIC_ROLE_LIKE_GAMMA = True

# Custom CSS (optional)
CUSTOM_CSS = """
.navbar-brand {
    color: #4f46e5 !important;
}
.dashboard-header h1 {
    color: #1f2937;
}
"""

# Logo Configuration
APP_NAME = "Property Monitor IF Analytics"
APP_ICON = "/static/assets/images/superset-logo.png"

# Language Configuration
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'},
    'uk': {'flag': 'ua', 'name': 'Українська'},
}

# Default Language
BABEL_DEFAULT_LOCALE = 'uk'
BABEL_DEFAULT_FOLDER = 'babel/translations'

# Row limit for SQL Lab
DEFAULT_SQLLAB_LIMIT = 1000
SQL_MAX_ROW = 100000

# Dashboard and chart configuration
DASHBOARD_AUTO_REFRESH_MODE = "fetch"
DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Don't refresh"],
    [10, "10 seconds"],
    [30, "30 seconds"], 
    [60, "1 minute"],
    [300, "5 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
]

# Filter Configuration
DEFAULT_FEATURE_FLAGS = {
    'ENABLE_EXPLORE_JSON_CSRF_PROTECTION': False,
    'ENABLE_EXPLORE_DRAG_AND_DROP': True,
}

# Data Upload Configuration
UPLOAD_FOLDER = str(Path('data/uploads').absolute())
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Alert and Report Configuration
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
WEBDRIVER_BASEURL = "http://localhost:8088/"

# Custom Security Manager (optional)
"""
from superset.security import SupersetSecurityManager

class CustomSecurityManager(SupersetSecurityManager):
    def __init__(self, appbuilder):
        super(CustomSecurityManager, self).__init__(appbuilder)

CUSTOM_SECURITY_MANAGER = CustomSecurityManager
"""
