#!/usr/bin/env python3
"""
Runtime Diagnostics Test Script
Perform the three critical tests to verify 404 fix and runtime diagnostics
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8080"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",
        "SUCCESS": "\033[92m", 
        "ERROR": "\033[91m",
        "TEST": "\033[95m"
    }
    color = colors.get(level, colors["INFO"])
    print(f"{color}[{timestamp}] {level}: {message}\033[0m")

def test_1_health_check():
    """Test 1: Health Check"""
    log("🧪 TEST 1: Health Check", "TEST")
    log("-" * 30, "INFO")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        log(f"Command: GET {BASE_URL}/health", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok'):
                    log(f"✅ Health OK: PID={data.get('pid')}, Version={data.get('version')}", "SUCCESS")
                    return True
                else:
                    log(f"❌ Health response missing 'ok': {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
                return False
        else:
            log(f"❌ HTTP {response.status_code}: {response.text[:200]}", "ERROR")
            return False
            
    except requests.ConnectionError:
        log("❌ Connection failed - FastAPI backend not running", "ERROR")
        log("Please start with: python cli/server.py", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_2_routes_verification():
    """Test 2: Routes Verification"""
    log("🧪 TEST 2: Routes Verification", "TEST")
    log("-" * 30, "INFO")
    
    try:
        response = requests.get(f"{BASE_URL}/__debug/routes", timeout=5)
        log(f"Command: GET {BASE_URL}/__debug/routes", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok'):
                    critical = data.get('critical_check', {})
                    total_routes = data.get('total_routes', 0)
                    
                    log(f"✅ Routes endpoint OK: {total_routes} total routes", "SUCCESS")
                    log(f"   • /scraper/start: {'✅' if critical.get('scraper_start') else '❌'}", "INFO")
                    log(f"   • /api/scraper/start: {'✅' if critical.get('api_scraper_start') else '❌'}", "INFO")
                    log(f"   • /health: {'✅' if critical.get('health') else '❌'}", "INFO")
                    
                    if critical.get('scraper_start') and critical.get('api_scraper_start'):
                        log("✅ All critical routes present", "SUCCESS")
                        return True
                    else:
                        log("❌ Missing critical routes", "ERROR")
                        return False
                else:
                    log(f"❌ Routes response missing 'ok': {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
                return False
        else:
            log(f"❌ HTTP {response.status_code}: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_3_scraper_start():
    """Test 3: Scraper Start"""
    log("🧪 TEST 3: Scraper Start (Dry Run)", "TEST")
    log("-" * 30, "INFO")
    
    try:
        test_body = {
            "listing_type": "sale",
            "max_pages": 1,
            "delay_ms": 1000,
            "headful": False
        }
        
        response = requests.post(
            f"{BASE_URL}/scraper/start",
            json=test_body,
            timeout=10
        )
        
        log(f"Command: POST {BASE_URL}/scraper/start", "INFO")
        log(f"Body: {json.dumps(test_body)}", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        try:
            data = response.json()
            log(f"Response: {json.dumps(data, indent=2)}", "INFO")
            
            if response.status_code == 202 and data.get('ok'):
                log(f"✅ Scraper start OK: {data.get('status')} (task: {data.get('task', 'no task')})", "SUCCESS")
                return True
            elif response.status_code == 409:
                log("✅ Scraper start OK: Already running (expected behavior)", "SUCCESS")
                return True
            else:
                log(f"❌ Scraper start failed: {response.status_code} {data.get('error', 'unknown error')}", "ERROR")
                return False
                
        except json.JSONDecodeError:
            log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_4_api_alias():
    """Test 4: API Alias Route"""
    log("🧪 TEST 4: API Alias Route", "TEST")
    log("-" * 30, "INFO")
    
    try:
        test_body = {
            "listing_type": "rent",
            "max_pages": 1,
            "delay_ms": 1000,
            "headful": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/scraper/start",
            json=test_body,
            timeout=10
        )
        
        log(f"Command: POST {BASE_URL}/api/scraper/start", "INFO")
        log(f"Body: {json.dumps(test_body)}", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        try:
            data = response.json()
            log(f"Response: {json.dumps(data, indent=2)}", "INFO")
            
            if response.status_code in [202, 409]:
                log("✅ API alias route works correctly", "SUCCESS")
                return True
            else:
                log(f"❌ API alias failed: {response.status_code}", "ERROR")
                return False
                
        except json.JSONDecodeError:
            log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_5_404_handling():
    """Test 5: 404 Error Handling"""
    log("🧪 TEST 5: 404 Error Handling", "TEST")
    log("-" * 30, "INFO")
    
    try:
        response = requests.get(f"{BASE_URL}/nonexistent/endpoint", timeout=5)
        log(f"Command: GET {BASE_URL}/nonexistent/endpoint", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 404:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok') == False and 'path' in data:
                    log("✅ 404 returns JSON with error info", "SUCCESS")
                    return True
                else:
                    log(f"❌ 404 JSON format incorrect: {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ 404 returned non-JSON: {response.text[:200]}", "ERROR")
                return False
        else:
            log(f"❌ Expected 404, got {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def main():
    """Run all tests"""
    log("🔧 RUNTIME DIAGNOSTICS TESTS", "TEST")
    log("=" * 50, "INFO")
    
    tests = [
        ("Health Check", test_1_health_check),
        ("Routes Verification", test_2_routes_verification), 
        ("Scraper Start", test_3_scraper_start),
        ("API Alias Route", test_4_api_alias),
        ("404 Error Handling", test_5_404_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log(f"❌ {test_name} crashed: {e}", "ERROR")
        
        log("", "INFO")  # Empty line between tests
    
    # Final results
    log("🎯 SUMMARY", "TEST")
    log("=" * 50, "INFO")
    log(f"📊 Results: {passed}/{total} tests passed", "INFO")
    
    if passed == total:
        log("🎉 ALL TESTS PASSED! Runtime diagnostics working correctly", "SUCCESS")
        log("✅ FastAPI backend is accessible and functional", "SUCCESS")
        log("✅ All critical routes are registered", "SUCCESS")
        log("✅ 404 errors return proper JSON", "SUCCESS")
        return True
    else:
        log(f"❌ {total - passed} test(s) failed", "ERROR")
        log("🔧 Make sure FastAPI backend is running: python cli/server.py", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
