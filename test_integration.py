#!/usr/bin/env python3
"""
Integration test script for the 5-module ML system.
Tests that all components can be imported and basic functionality works.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    tests = [
        ("Botasaurus Scraper", "scraper.olx_scraper", "OLXScraper"),
        ("LightAutoML Training", "ml.laml.train", "main"),
        ("Prophet Forecasting", "analytics.prophet.forecast", "generate_forecast"),
        ("Streamlit App", "app.streamlit_app", "main"),
        ("CLI Interface", "property_monitor_cli", "main")
    ]
    
    results = []
    for name, module_path, function_name in tests:
        try:
            module = __import__(module_path, fromlist=[function_name])
            getattr(module, function_name)
            print(f"  ✅ {name}: OK")
            results.append(True)
        except ImportError as e:
            print(f"  ❌ {name}: Import failed - {e}")
            results.append(False)
        except AttributeError as e:
            print(f"  ⚠️  {name}: Function not found - {e}")
            results.append(False)
        except Exception as e:
            print(f"  ❌ {name}: Unexpected error - {e}")
            results.append(False)
    
    return all(results)

def test_database():
    """Test database connectivity"""
    print("\n🗄️  Testing database connectivity...")
    
    try:
        import sqlite3
        conn = sqlite3.connect("glow_nest.db")
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        expected_tables = ['properties', 'street_district_map', 'activity_logs']
        found_tables = [table[0] for table in tables]
        
        for table in expected_tables:
            if table in found_tables:
                print(f"  ✅ Table '{table}': OK")
            else:
                print(f"  ❌ Table '{table}': Missing")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        "scraper",
        "ml/laml", 
        "analytics/prophet",
        "app",
        "superset",
        "data",
        "models",
        "reports"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"  ✅ {directory}/: OK")
        else:
            print(f"  ❌ {directory}/: Missing")
            all_exist = False
    
    return all_exist

def test_cli_help():
    """Test that the CLI shows help correctly"""
    print("\n⚡ Testing CLI interface...")
    
    try:
        import property_monitor_cli
        # This should not raise an exception
        print("  ✅ CLI module loads: OK")
        return True
    except Exception as e:
        print(f"  ❌ CLI test failed: {e}")
        return False

def test_requirements():
    """Test that key dependencies are available"""
    print("\n📦 Testing key dependencies...")
    
    key_deps = [
        ("botasaurus", "Web scraping framework"),
        ("lightautoml", "Automated ML"),
        ("prophet", "Time series forecasting"), 
        ("streamlit", "Web interface"),
        ("pandas", "Data manipulation"),
        ("sqlite3", "Database (built-in)"),
        ("rich", "Console output")
    ]
    
    all_available = True
    for dep, description in key_deps:
        try:
            if dep == "sqlite3":
                import sqlite3
            else:
                __import__(dep)
            print(f"  ✅ {dep}: OK ({description})")
        except ImportError:
            print(f"  ❌ {dep}: Missing ({description})")
            all_available = False
    
    return all_available

def main():
    """Run all integration tests"""
    print("🔥 GLOW NEST XGB - Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Schema", test_database),
        ("Directory Structure", test_directories),
        ("CLI Interface", test_cli_help),
        ("Dependencies", test_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System ready for use.")
        print("\n🚀 Next steps:")
        print("   1. python property_monitor_cli.py scraper start")
        print("   2. python property_monitor_cli.py ml train")
        print("   3. python property_monitor_cli.py web start")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        print("\n🔧 Common fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Run: python setup_ml_system.py")
        print("   - Check Python version (3.8+ required)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
