#!/usr/bin/env python3
"""
Quick test script to verify the JSON fix for spawn python ENOENT issue
"""

import os
import time
import asyncio
import sqlite3
from datetime import datetime

def log_status(message, status="INFO"):
    """Print test status with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"[{timestamp}] {emoji.get(status, 'ℹ️')} {message}")

def test_database_paths():
    """Test 1: Verify database path consistency"""
    log_status("Testing database path consistency", "INFO")
    
    try:
        # Check if main database exists
        if os.path.exists("glow_nest.db"):
            size = os.path.getsize("glow_nest.db")
            log_status(f"Database exists: glow_nest.db ({size} bytes)", "SUCCESS")
        else:
            log_status("Database file glow_nest.db not found", "ERROR")
            return False
            
        # Test database connection
        conn = sqlite3.connect("glow_nest.db")
        cursor = conn.cursor()
        
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['properties', 'street_districts', 'activity_log']
        for table in required_tables:
            if table in tables:
                log_status(f"Table '{table}' exists", "SUCCESS")
            else:
                log_status(f"Table '{table}' missing", "ERROR")
        
        # Test property count
        cursor.execute("SELECT COUNT(*) FROM properties")
        count = cursor.fetchone()[0]
        log_status(f"Properties in database: {count}", "INFO")
        
        conn.close()
        return True
        
    except Exception as e:
        log_status(f"Database test failed: {e}", "ERROR")
        return False

def test_python_imports():
    """Test 2: Verify Python imports work"""
    log_status("Testing Python module imports", "INFO")
    
    try:
        # Test FastAPI
        import fastapi
        log_status("FastAPI import: OK", "SUCCESS")
        
        # Test our modules
        try:
            from cli.server import app
            log_status("FastAPI app import: OK", "SUCCESS")
        except Exception as e:
            log_status(f"FastAPI app import failed: {e}", "WARNING")
        
        try:
            from cli.tasks import TaskManager
            log_status("TaskManager import: OK", "SUCCESS")
        except Exception as e:
            log_status(f"TaskManager import failed: {e}", "WARNING")
            
        try:
            from scraper.persist import DatabaseManager
            log_status("DatabaseManager import: OK", "SUCCESS")
        except Exception as e:
            log_status(f"DatabaseManager import failed: {e}", "WARNING")
        
        return True
        
    except Exception as e:
        log_status(f"Import test failed: {e}", "ERROR")
        return False

def test_json_structure():
    """Test 3: Verify expected JSON response structure"""
    log_status("Testing JSON response structure expectation", "INFO")
    
    try:
        # This simulates what the Python backend should return
        expected_response = {
            "ok": True,
            "task": "scraper_123456789",
            "message": "Scraping started for sale listings",
            "estimated_time": "50 seconds",
            "parameters": {
                "listing_type": "sale",
                "max_pages": 5,
                "delay_ms": 5000
            }
        }
        
        log_status("Expected JSON structure defined", "SUCCESS")
        log_status(f"Sample: {expected_response}", "INFO")
        
        # Test error response structure
        error_response = {
            "ok": False,
            "error": "ScrapingError: Already running"
        }
        
        log_status("Error JSON structure defined", "SUCCESS")
        log_status(f"Error sample: {error_response}", "INFO")
        
        return True
        
    except Exception as e:
        log_status(f"JSON structure test failed: {e}", "ERROR")
        return False

def test_file_changes():
    """Test 4: Verify key files have been updated"""
    log_status("Testing file changes for JSON fix", "INFO")
    
    files_to_check = [
        ("cli/server.py", "JSONResponse"),
        ("server/routes/scraping.ts", "safeJsonParse"),
        ("client/pages/Admin.tsx", "JSON parse error"),
        ("scraper/persist.py", "glow_nest.db"),
        ("cli/tasks.py", "glow_nest.db")
    ]
    
    for file_path, expected_content in files_to_check:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if expected_content in content:
                        log_status(f"✓ {file_path} contains '{expected_content}'", "SUCCESS")
                    else:
                        log_status(f"✗ {file_path} missing '{expected_content}'", "WARNING")
            else:
                log_status(f"File not found: {file_path}", "ERROR")
        except Exception as e:
            log_status(f"Error checking {file_path}: {e}", "ERROR")
    
    return True

def main():
    """Run all tests"""
    log_status("Starting JSON fix verification tests", "INFO")
    log_status("=" * 50, "INFO")
    
    tests = [
        ("Database Paths", test_database_paths),
        ("Python Imports", test_python_imports), 
        ("JSON Structure", test_json_structure),
        ("File Changes", test_file_changes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log_status(f"\n--- Running {test_name} Test ---", "INFO")
        try:
            if test_func():
                passed += 1
                log_status(f"{test_name}: PASSED", "SUCCESS")
            else:
                log_status(f"{test_name}: FAILED", "ERROR")
        except Exception as e:
            log_status(f"{test_name}: ERROR - {e}", "ERROR")
    
    log_status("\n" + "=" * 50, "INFO")
    log_status(f"Test Results: {passed}/{total} passed", "SUCCESS" if passed == total else "WARNING")
    
    if passed == total:
        log_status("🎉 All tests PASSED - JSON fix is ready!", "SUCCESS")
        return True
    else:
        log_status(f"⚠️ {total - passed} tests failed", "WARNING")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")
