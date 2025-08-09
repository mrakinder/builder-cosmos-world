#!/usr/bin/env python3
"""
Glow Nest XGB System Startup Script
Initializes and starts the complete 5-module system
"""

import os
import sys
import subprocess
import time
import asyncio
from pathlib import Path


def print_banner():
    """Display startup banner"""
    print("""
🏠 ═══════════════════════════════════════════════════════════════════════════════ 🏠
    
     ██████╗ ██╗      ██████╗ ██╗    ██╗    ███╗   ██╗███████╗███████╗████████╗
    ██╔════╝ ██║     ██╔═══██╗██║    ██║    ████╗  ██║██╔════╝██╔════╝╚══██╔══╝
    ██║  ███╗██║     ██║   ██║██║ █╗ ██║    ██╔██╗ ██║█████╗  ███████╗   ██║   
    ██║   ██║██║     ██║   ██║██║███╗██║    ██║╚██╗██║██╔══╝  ╚════██║   ██║   
    ╚██████╔╝███████╗╚██████╔╝╚███╔███╔╝    ██║ ╚████║███████╗███████║   ██║   
     ╚═════╝ ╚══════╝ ╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═══╝╚══════╝╚══════╝   ╚═╝   

                        🧠 XGB - 5-Module Real Estate Analytics System
                              Івано-Франківськ • Production Ready

🏠 ═══════════════════════════════════════════════════════════════════════════════ 🏠
""")


def check_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check required files
    required_files = [
        "requirements.txt",
        "cli/server.py", 
        "admin/panel/index.html",
        "app/streamlit_app.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
    print("✅ All required files present")
    
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run manually: pip install -r requirements.txt")
        return False


def setup_database():
    """Initialize database schema"""
    print("\n🗄️ Setting up database...")
    
    try:
        from cli.utils import ensure_database_schema
        result = ensure_database_schema()
        
        if result:
            print("✅ Database schema initialized")
            return True
        else:
            print("❌ Database setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        return False


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "data",
        "models", 
        "reports/prophet",
        "cli/logs",
        "scraper/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created")


def start_api_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting API server...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "cli/server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ API server started on http://localhost:8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        return None


def show_access_info():
    """Display access information"""
    print("\n" + "=" * 70)
    print("🎉 GLOW NEST XGB SYSTEM READY!")
    print("=" * 70)
    
    print("\n🎛️ CONTROL INTERFACES:")
    print("   📊 Admin Panel:       http://localhost:8080/admin/panel/")
    print("   ⚡ API Documentation: http://localhost:8080/docs")
    print("   📈 System Status:     http://localhost:8080/system/status")
    
    print("\n🌐 PUBLIC INTERFACES:")
    print("   🏠 Property Evaluation: http://localhost:8501 (after starting via admin)")
    print("   📊 Business Analytics:  http://localhost:8088 (Superset - manual setup)")
    
    print("\n🎮 QUICK START:")
    print("   1. Open Admin Panel (link above)")
    print("   2. Click 'Парсинг (Продаж)' to collect data")
    print("   3. Click 'Тренувати модель' to train ML")
    print("   4. Click 'Запустити Streamlit' for public interface")
    print("   5. Monitor progress in real-time!")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("   • Run tests: python test_system.py")
    print("   • Check logs in: cli/logs/")
    print("   • API health: curl http://localhost:8080/health")
    
    print("\n💡 FEATURES:")
    print("   ✅ 5 Complete Modules (Scraper, ML, Prophet, Streamlit, Superset)")
    print("   ✅ Button-Based Control (No CLI needed)")
    print("   ✅ Real-Time Progress Tracking")
    print("   ✅ Mobile-Responsive Design")
    print("   ✅ Anti-Detection Scraping")
    print("   ✅ Live Event Monitoring")
    
    print("\n" + "=" * 70)


def main():
    """Main startup sequence"""
    print_banner()
    
    # Pre-flight checks
    if not check_requirements():
        print("\n❌ System requirements not met. Please fix the issues above.")
        sys.exit(1)
    
    # Setup sequence
    steps = [
        ("Installing Dependencies", install_dependencies),
        ("Setting Up Database", setup_database),
        ("Creating Directories", create_directories)
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ {step_name} failed. Please check the errors above.")
            sys.exit(1)
    
    # Start server
    server_process = start_api_server()
    
    if server_process is None:
        print("\n❌ Failed to start API server. Please check the errors above.")
        sys.exit(1)
    
    # Show access information
    show_access_info()
    
    # Keep script running
    try:
        print("\n⌨️  Press Ctrl+C to stop the system")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down system...")
        server_process.terminate()
        server_process.wait()
        print("✅ System stopped. Goodbye!")


if __name__ == "__main__":
    main()
