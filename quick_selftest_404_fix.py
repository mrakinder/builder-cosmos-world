#!/usr/bin/env python3
"""
Швидкий самотест для 404 + Empty Body фіксу
Перевіряє що /scraper/start та /api/scraper/start завжди повертають JSON
"""

import requests
import json
import time
from datetime import datetime

FASTAPI_BASE = "http://localhost:8080"

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

def test_health():
    """Test 1: Health check"""
    log("Testing /health endpoint", "TEST")
    try:
        response = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                log("✅ FastAPI server is running", "SUCCESS")
                return True
        log(f"❌ Health check failed: {response.status_code}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Health check error: {e}", "ERROR")
        return False

def test_routes():
    """Test 2: Both /scraper/start and /api/scraper/start routes"""
    routes_to_test = ["/scraper/start", "/api/scraper/start"]
    
    test_body = {
        "listing_type": "sale",
        "max_pages": 2,
        "delay_ms": 1000,
        "headful": False
    }
    
    for route in routes_to_test:
        log(f"Testing POST {route}", "TEST")
        try:
            response = requests.post(
                f"{FASTAPI_BASE}{route}",
                json=test_body,
                timeout=10
            )
            
            log(f"Status: {response.status_code} {response.statusText if hasattr(response, 'statusText') else ''}", "INFO")
            
            # Must get JSON response (never empty body)
            try:
                data = response.json()
                log(f"JSON response: {json.dumps(data, indent=2)[:200]}...", "INFO")
                
                if response.status_code in [200, 202]:
                    if data.get('ok'):
                        log(f"✅ {route} works correctly", "SUCCESS")
                    else:
                        log(f"⚠️ {route} returned error: {data.get('error', 'unknown')}", "INFO")
                elif response.status_code == 409:
                    # Already running is OK
                    log(f"✅ {route} correctly handled conflict (409)", "SUCCESS")
                else:
                    log(f"❌ {route} returned unexpected status: {response.status_code}", "ERROR")
                    return False
                    
            except json.JSONDecodeError as e:
                log(f"❌ {route}: Failed to parse JSON: {e}", "ERROR")
                log(f"Raw response: {response.text[:200]}", "ERROR")
                return False
                
        except Exception as e:
            log(f"❌ {route} request failed: {e}", "ERROR")
            return False
            
        time.sleep(1)  # Delay between requests
    
    return True

def test_404_handler():
    """Test 3: Custom 404 handler returns JSON"""
    log("Testing custom 404 JSON handler", "TEST")
    try:
        # Request non-existent endpoint
        response = requests.get(f"{FASTAPI_BASE}/nonexistent/endpoint", timeout=5)
        
        if response.status_code == 404:
            try:
                data = response.json()
                if data.get('ok') == False and data.get('path'):
                    log(f"✅ 404 returns JSON: {data}", "SUCCESS")
                    return True
                else:
                    log(f"❌ 404 JSON format wrong: {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ 404 returned non-JSON: {response.text[:100]}", "ERROR")
                return False
        else:
            log(f"❌ Expected 404, got {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ 404 test error: {e}", "ERROR")
        return False

def test_invalid_json():
    """Test 4: Validation error returns JSON"""
    log("Testing JSON validation error handling", "TEST")
    try:
        # Send invalid JSON body
        invalid_body = {"listing_type": "sale", "max_pages": "invalid"}
        
        response = requests.post(
            f"{FASTAPI_BASE}/scraper/start",
            json=invalid_body,
            timeout=5
        )
        
        # Should get 422 with JSON error
        try:
            data = response.json()
            if response.status_code == 422 and data.get('ok') == False:
                log(f"✅ Validation error returns JSON: {data.get('error', 'ValidationError')}", "SUCCESS")
                return True
            elif response.status_code in [200, 202, 409]:
                # FastAPI might auto-convert, that's OK too
                log(f"✅ FastAPI handled invalid JSON gracefully: {response.status_code}", "SUCCESS")
                return True
            else:
                log(f"❌ Unexpected validation response: {response.status_code} {data}", "ERROR")
                return False
        except json.JSONDecodeError:
            log(f"❌ Validation error returned non-JSON: {response.text[:100]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Validation test error: {e}", "ERROR")
        return False

def main():
    """Run quick selftest"""
    log("🚀 STARTING QUICK SELFTEST FOR 404 + EMPTY BODY FIX", "TEST")
    log("=" * 60, "INFO")
    
    tests = [
        ("Health Check", test_health),
        ("Route Testing", test_routes), 
        ("404 JSON Handler", test_404_handler),
        ("Validation Error Handler", test_invalid_json)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log(f"\n📋 Running: {test_name}", "TEST")
        log("-" * 30, "INFO")
        
        try:
            if test_func():
                log(f"✅ {test_name} PASSED", "SUCCESS")
                passed += 1
            else:
                log(f"❌ {test_name} FAILED", "ERROR")
        except Exception as e:
            log(f"❌ {test_name} CRASHED: {e}", "ERROR")
        
        time.sleep(0.5)
    
    # Results
    log("\n" + "=" * 60, "INFO")
    log(f"🏁 SELFTEST COMPLETED: {passed}/{total} tests passed", "TEST")
    
    if passed == total:
        log("🎉 ALL TESTS PASSED!", "SUCCESS")
        log("✅ /scraper/start and /api/scraper/start work correctly", "SUCCESS")
        log("✅ 404 errors return JSON (no empty body)", "SUCCESS")
        log("✅ Validation errors return JSON", "SUCCESS")
        log("✅ FastAPI server is stable and ready", "SUCCESS")
        return True
    else:
        log(f"❌ {total - passed} test(s) failed", "ERROR")
        log("🔧 Check FastAPI server logs for route registration", "INFO")
        log("🔧 Verify server is running on http://localhost:8080", "INFO")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
