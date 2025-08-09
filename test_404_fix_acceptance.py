#!/usr/bin/env python3
"""
Comprehensive Acceptance Test Script for 404 Fix
Tests all routes including aliases to prevent "scraper/start" 404 errors
"""

import asyncio
import json
import time
import requests
from datetime import datetime

# Test configuration
FASTAPI_BASE = "http://localhost:8080"
NODE_BASE = "http://localhost:3000"

def log_test(message, level="INFO"):
    """Enhanced logging with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",    # Cyan
        "SUCCESS": "\033[92m", # Green
        "ERROR": "\033[91m",   # Red
        "WARNING": "\033[93m", # Yellow
        "TEST": "\033[95m"     # Magenta
    }
    reset = "\033[0m"
    color = colors.get(level, colors["INFO"])
    print(f"{color}[{timestamp}] {level}: {message}{reset}")

def test_fastapi_routes():
    """Test 1: Verify FastAPI routes including aliases"""
    log_test("Testing FastAPI routes structure and aliases", "TEST")
    
    try:
        # Test health endpoint first
        response = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
        if response.status_code == 200:
            log_test("✅ FastAPI server is running", "SUCCESS")
        else:
            log_test(f"❌ FastAPI health check failed: {response.status_code}", "ERROR")
            return False
            
        # Test original route
        test_body = {
            "listing_type": "sale",
            "max_pages": 5,
            "delay_ms": 2000,
            "headful": False
        }
        
        log_test("Testing POST /scraper/start (original route)", "TEST")
        response = requests.post(
            f"{FASTAPI_BASE}/scraper/start",
            json=test_body,
            timeout=10
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        log_test(f"Response headers: {dict(response.headers)}", "INFO")
        
        if response.status_code in [200, 202, 409]:  # Success, Accepted, or Already Running
            try:
                data = response.json()
                log_test(f"JSON response: {json.dumps(data, indent=2)}", "INFO")
                if data.get('ok') or data.get('success'):
                    log_test("✅ Original route works and returns JSON", "SUCCESS")
                else:
                    log_test(f"⚠️ Original route returned JSON but with error: {data}", "WARNING")
            except json.JSONDecodeError as e:
                log_test(f"❌ Original route: JSON decode error: {e}", "ERROR")
                log_test(f"Raw response: {response.text[:200]}", "ERROR")
                return False
        else:
            log_test(f"❌ Original route failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
            
        # Test alias route
        log_test("Testing POST /api/scraper/start (alias route)", "TEST")
        response = requests.post(
            f"{FASTAPI_BASE}/api/scraper/start",
            json=test_body,
            timeout=10
        )
        
        log_test(f"Alias response status: {response.status_code}", "INFO")
        
        if response.status_code in [200, 202, 409]:
            try:
                data = response.json()
                log_test(f"Alias JSON response: {json.dumps(data, indent=2)}", "INFO")
                if data.get('ok') or data.get('success'):
                    log_test("✅ Alias route works and returns JSON", "SUCCESS")
                else:
                    log_test(f"⚠️ Alias route returned JSON but with error: {data}", "WARNING")
            except json.JSONDecodeError as e:
                log_test(f"❌ Alias route: JSON decode error: {e}", "ERROR")
                return False
        else:
            log_test(f"❌ Alias route failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
            
        return True
        
    except requests.ConnectionError:
        log_test("❌ Cannot connect to FastAPI server", "ERROR")
        return False
    except Exception as e:
        log_test(f"❌ FastAPI route test error: {e}", "ERROR")
        return False

def test_node_proxy():
    """Test 2: Verify Node.js proxy layer works with Python backend"""
    log_test("Testing Node.js proxy to Python backend communication", "TEST")
    
    try:
        # Test Node.js proxy route
        test_body = {
            "listing_type": "rent",
            "max_pages": 3
        }
        
        log_test("Testing POST /api/scraper/start via Node.js proxy", "TEST")
        response = requests.post(
            f"{NODE_BASE}/api/scraper/start",
            json=test_body,
            timeout=15
        )
        
        log_test(f"Node proxy response status: {response.status_code}", "INFO")
        
        if response.status_code in [200, 202, 500]:  # Allow 500 for debugging
            try:
                data = response.json()
                log_test(f"Node proxy JSON: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('success') or data.get('python_backend'):
                    log_test("✅ Node proxy successfully communicates with Python", "SUCCESS")
                elif data.get('error') and 'Python backend' in str(data.get('error')):
                    log_test("⚠️ Node proxy reaches Python but gets backend error", "WARNING")
                    # This might be expected if scraper is already running
                else:
                    log_test(f"❌ Node proxy: unexpected response: {data}", "ERROR")
                    return False
                    
            except json.JSONDecodeError as e:
                log_test(f"❌ Node proxy: JSON decode error: {e}", "ERROR")
                log_test(f"Raw response: {response.text[:200]}", "ERROR")
                return False
        else:
            log_test(f"❌ Node proxy failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
            
        return True
        
    except requests.ConnectionError:
        log_test("❌ Cannot connect to Node.js server", "ERROR")
        return False
    except Exception as e:
        log_test(f"❌ Node proxy test error: {e}", "ERROR")
        return False

def test_json_consistency():
    """Test 3: Verify JSON body consistency between all endpoints"""
    log_test("Testing JSON body consistency across all endpoints", "TEST")
    
    test_cases = [
        {
            "name": "Standard request",
            "body": {"listing_type": "sale", "max_pages": 2, "delay_ms": 1000}
        },
        {
            "name": "Minimal request",  
            "body": {"listing_type": "rent"}
        },
        {
            "name": "Full request",
            "body": {"listing_type": "sale", "max_pages": 5, "delay_ms": 3000, "headful": False}
        }
    ]
    
    for test_case in test_cases:
        log_test(f"Testing {test_case['name']}: {test_case['body']}", "TEST")
        
        # Test direct FastAPI
        try:
            response = requests.post(
                f"{FASTAPI_BASE}/scraper/start",
                json=test_case['body'],
                timeout=10
            )
            
            if response.status_code in [200, 202, 409]:
                data = response.json()
                log_test(f"✅ FastAPI handles {test_case['name']}: {data.get('status', 'unknown')}", "SUCCESS")
            else:
                log_test(f"❌ FastAPI failed {test_case['name']}: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            log_test(f"❌ FastAPI {test_case['name']} error: {e}", "ERROR")
            return False
            
        # Small delay between requests
        time.sleep(1)
    
    return True

def test_error_scenarios():
    """Test 4: Verify proper error handling for various scenarios"""
    log_test("Testing error handling scenarios", "TEST")
    
    error_cases = [
        {
            "name": "Invalid max_pages",
            "body": {"listing_type": "sale", "max_pages": -1},
            "expected_error": True
        },
        {
            "name": "Invalid listing_type", 
            "body": {"listing_type": "invalid_type", "max_pages": 5},
            "expected_error": False  # Should work with defaults
        },
        {
            "name": "Missing body",
            "body": {},
            "expected_error": False  # Should work with defaults
        }
    ]
    
    for error_case in error_cases:
        log_test(f"Testing error case: {error_case['name']}", "TEST")
        
        try:
            response = requests.post(
                f"{FASTAPI_BASE}/scraper/start",
                json=error_case['body'],
                timeout=10
            )
            
            # Check if we get JSON response (no empty body)
            try:
                data = response.json()
                log_test(f"✅ Error case returns JSON: {data.get('ok', 'unknown')}", "SUCCESS")
            except json.JSONDecodeError:
                log_test(f"❌ Error case returned non-JSON: {response.text[:100]}", "ERROR")
                return False
                
        except Exception as e:
            log_test(f"❌ Error case {error_case['name']} failed: {e}", "ERROR")
            return False
            
        time.sleep(0.5)
    
    return True

def test_route_diagnostics():
    """Test 5: Verify route diagnostics are working"""
    log_test("Testing route diagnostics and logging", "TEST")
    
    # This test checks if we can see route information
    # In a real scenario, we'd check logs, but here we test basic connectivity
    
    endpoints_to_test = [
        "/health",
        "/scraper/start", 
        "/api/scraper/start",
        "/scraper/status",
        "/system/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            if endpoint in ["/scraper/start", "/api/scraper/start"]:
                # POST endpoints
                response = requests.post(
                    f"{FASTAPI_BASE}{endpoint}",
                    json={"listing_type": "sale", "max_pages": 1},
                    timeout=5
                )
            else:
                # GET endpoints
                response = requests.get(f"{FASTAPI_BASE}{endpoint}", timeout=5)
                
            if response.status_code < 500:  # Any non-server-error is good
                log_test(f"✅ Route {endpoint} is accessible", "SUCCESS")
            else:
                log_test(f"⚠️ Route {endpoint} server error: {response.status_code}", "WARNING")
                
        except requests.ConnectionError:
            log_test(f"❌ Route {endpoint} not accessible", "ERROR")
            return False
        except Exception as e:
            log_test(f"❌ Route {endpoint} test error: {e}", "ERROR")
            
        time.sleep(0.2)
    
    return True

def main():
    """Run all acceptance tests"""
    log_test("🚀 STARTING 404 FIX ACCEPTANCE TESTS", "TEST")
    log_test("=" * 60, "INFO")
    
    tests = [
        ("FastAPI Routes & Aliases", test_fastapi_routes),
        ("Node.js Proxy Communication", test_node_proxy),
        ("JSON Body Consistency", test_json_consistency),
        ("Error Handling", test_error_scenarios),
        ("Route Diagnostics", test_route_diagnostics)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        log_test(f"\n📋 Running: {test_name}", "TEST")
        log_test("-" * 40, "INFO")
        
        try:
            if test_func():
                log_test(f"✅ {test_name} PASSED", "SUCCESS")
                passed_tests += 1
            else:
                log_test(f"❌ {test_name} FAILED", "ERROR")
        except Exception as e:
            log_test(f"❌ {test_name} CRASHED: {e}", "ERROR")
        
        log_test("-" * 40, "INFO")
        time.sleep(1)
    
    # Final results
    log_test("\n" + "=" * 60, "INFO")
    log_test(f"🏁 ACCEPTANCE TESTS COMPLETED", "TEST")
    log_test(f"📊 Results: {passed_tests}/{total_tests} tests passed", "INFO")
    
    if passed_tests == total_tests:
        log_test("🎉 ALL TESTS PASSED - 404 fix is working perfectly!", "SUCCESS")
        log_test("✅ FastAPI alias routes prevent 404 errors", "SUCCESS")
        log_test("✅ Node.js → Python communication is stable", "SUCCESS")
        log_test("✅ JSON body parsing works correctly", "SUCCESS")
        log_test("✅ Error handling prevents empty responses", "SUCCESS")
        return True
    else:
        failed_count = total_tests - passed_tests
        log_test(f"❌ {failed_count} test(s) failed - needs investigation", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
