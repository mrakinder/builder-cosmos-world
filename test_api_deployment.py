#!/usr/bin/env python3
"""
Comprehensive Acceptance Tests for Fly.dev API Deployment
Tests the complete flow: Frontend → Node.js → FastAPI → Database
"""

import requests
import json
import time
import sys
from datetime import datetime

# Production URLs
FRONTEND_URL = "https://dea706f0b3dd454188742d996e9d262a-58026be633ce45519cb96963e.fly.dev"
API_URL = "https://glow-nest-api.fly.dev"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",
        "SUCCESS": "\033[92m", 
        "ERROR": "\033[91m",
        "TEST": "\033[95m",
        "WARNING": "\033[93m"
    }
    color = colors.get(level, colors["INFO"])
    print(f"{color}[{timestamp}] {level}: {message}\033[0m")

def test_1_api_health():
    """Test 1: API Health Check"""
    log("🧪 TEST 1: API Health Check", "TEST")
    log("-" * 40, "INFO")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        log(f"Request: GET {API_URL}/health", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok'):
                    log(f"✅ API Health OK: PID={data.get('pid')}, Version={data.get('version', 'unknown')}", "SUCCESS")
                    return True
                else:
                    log(f"❌ API Health response missing 'ok': {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
                return False
        else:
            log(f"❌ HTTP {response.status_code}: {response.text[:200]}", "ERROR")
            return False
            
    except requests.ConnectionError:
        log("❌ Connection failed - API not deployed or not accessible", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_2_api_routes():
    """Test 2: API Routes Verification"""
    log("🧪 TEST 2: API Routes Verification", "TEST")
    log("-" * 40, "INFO")
    
    try:
        response = requests.get(f"{API_URL}/__debug/routes", timeout=10)
        log(f"Request: GET {API_URL}/__debug/routes", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok'):
                    critical = data.get('critical_check', {})
                    total_routes = data.get('total_routes', 0)
                    
                    log(f"✅ API Routes OK: {total_routes} total routes", "SUCCESS")
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

def test_3_api_scraper_start():
    """Test 3: Direct API Scraper Start"""
    log("🧪 TEST 3: Direct API Scraper Start", "TEST")
    log("-" * 40, "INFO")
    
    try:
        test_body = {
            "listing_type": "sale",
            "max_pages": 1,
            "delay_ms": 1000,
            "headful": False
        }
        
        response = requests.post(
            f"{API_URL}/scraper/start",
            json=test_body,
            timeout=15
        )
        
        log(f"Request: POST {API_URL}/scraper/start", "INFO")
        log(f"Body: {json.dumps(test_body)}", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        try:
            data = response.json()
            log(f"Response: {json.dumps(data, indent=2)}", "INFO")
            
            if response.status_code == 202 and data.get('ok'):
                log(f"✅ Direct API start OK: {data.get('status')} (task: {data.get('task', 'no task')})", "SUCCESS")
                return True
            elif response.status_code == 409:
                log("✅ Direct API start OK: Already running (expected behavior)", "SUCCESS")
                return True
            else:
                log(f"❌ Direct API start failed: {response.status_code} {data.get('error', 'unknown error')}", "ERROR")
                return False
                
        except json.JSONDecodeError:
            log(f"❌ Non-JSON response: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_4_frontend_connectivity():
    """Test 4: Frontend Connectivity"""
    log("🧪 TEST 4: Frontend Connectivity", "TEST")
    log("-" * 40, "INFO")
    
    try:
        response = requests.get(f"{FRONTEND_URL}/", timeout=10)
        log(f"Request: GET {FRONTEND_URL}/", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            content = response.text
            if "Hello world project" in content and "<div id=\"root\"></div>" in content:
                log("✅ Frontend is accessible and serving React app", "SUCCESS")
                return True
            else:
                log(f"❌ Frontend content unexpected: {content[:200]}", "ERROR")
                return False
        else:
            log(f"❌ Frontend not accessible: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_5_node_proxy():
    """Test 5: Node.js Proxy to API"""
    log("🧪 TEST 5: Node.js Proxy to API", "TEST")
    log("-" * 40, "INFO")
    
    try:
        # Test health endpoint through Node.js proxy
        response = requests.get(f"{FRONTEND_URL}/api/health", timeout=15)
        log(f"Request: GET {FRONTEND_URL}/api/health", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log(f"Response: {json.dumps(data, indent=2)}", "INFO")
                
                if data.get('ok'):
                    log("✅ Node.js proxy to API working", "SUCCESS")
                    return True
                else:
                    log(f"❌ Node proxy returned invalid data: {data}", "ERROR")
                    return False
            except json.JSONDecodeError:
                log(f"❌ Node proxy returned non-JSON: {response.text[:200]}", "ERROR")
                return False
        else:
            log(f"❌ Node proxy failed: {response.status_code} {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_6_cors_headers():
    """Test 6: CORS Headers"""
    log("🧪 TEST 6: CORS Headers", "TEST")
    log("-" * 40, "INFO")
    
    try:
        # Test preflight OPTIONS request
        response = requests.options(
            f"{API_URL}/scraper/start",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        log(f"Request: OPTIONS {API_URL}/scraper/start", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        log(f"Headers: {dict(response.headers)}", "INFO")
        
        if response.status_code in [200, 204]:
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_methods = response.headers.get("Access-Control-Allow-Methods")
            
            if cors_origin and cors_methods:
                log(f"✅ CORS configured: Origin={cors_origin}, Methods={cors_methods}", "SUCCESS")
                return True
            else:
                log("❌ CORS headers missing", "ERROR")
                return False
        else:
            log(f"❌ CORS preflight failed: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def test_7_end_to_end():
    """Test 7: End-to-End Scraper Flow"""
    log("🧪 TEST 7: End-to-End Scraper Flow", "TEST")
    log("-" * 40, "INFO")
    
    try:
        # Test scraper start through Node.js proxy
        test_body = {
            "listing_type": "rent",
            "max_pages": 1,
            "delay_ms": 500,
            "headful": False
        }
        
        response = requests.post(
            f"{FRONTEND_URL}/api/scraper/start",
            json=test_body,
            timeout=20
        )
        
        log(f"Request: POST {FRONTEND_URL}/api/scraper/start", "INFO")
        log(f"Body: {json.dumps(test_body)}", "INFO")
        log(f"Status: {response.status_code}", "INFO")
        
        try:
            data = response.json()
            log(f"Response: {json.dumps(data, indent=2)}", "INFO")
            
            if response.status_code in [200, 202, 409]:
                if data.get('success') or data.get('ok') or (response.status_code == 409):
                    log("✅ End-to-end flow working: Frontend → Node → API", "SUCCESS")
                    return True
                else:
                    log(f"❌ End-to-end flow error: {data.get('error', 'unknown')}", "ERROR")
                    return False
            else:
                log(f"❌ End-to-end flow failed: {response.status_code}", "ERROR")
                return False
                
        except json.JSONDecodeError:
            log(f"❌ End-to-end returned non-JSON: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        return False

def main():
    """Run all acceptance tests"""
    log("🚀 COMPREHENSIVE ACCEPTANCE TESTS FOR API DEPLOYMENT", "TEST")
    log("=" * 60, "INFO")
    log(f"Frontend URL: {FRONTEND_URL}", "INFO")
    log(f"API URL: {API_URL}", "INFO")
    log("=" * 60, "INFO")
    
    tests = [
        ("API Health Check", test_1_api_health),
        ("API Routes Verification", test_2_api_routes),
        ("Direct API Scraper Start", test_3_api_scraper_start),
        ("Frontend Connectivity", test_4_frontend_connectivity),
        ("Node.js Proxy to API", test_5_node_proxy),
        ("CORS Headers", test_6_cors_headers),
        ("End-to-End Scraper Flow", test_7_end_to_end)
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
    log("🎯 ACCEPTANCE TEST RESULTS", "TEST")
    log("=" * 60, "INFO")
    log(f"📊 Results: {passed}/{total} tests passed", "INFO")
    
    if passed == total:
        log("🎉 ALL ACCEPTANCE TESTS PASSED!", "SUCCESS")
        log("✅ API is deployed and fully functional", "SUCCESS")
        log("✅ Frontend → Node.js → FastAPI communication working", "SUCCESS")
        log("✅ CORS properly configured", "SUCCESS")
        log("✅ All critical endpoints accessible", "SUCCESS")
        log("✅ System ready for production use", "SUCCESS")
        return True
    else:
        failed = total - passed
        log(f"❌ {failed} test(s) failed", "ERROR")
        
        if passed == 0:
            log("🔧 API might not be deployed yet. Run: fly deploy -c fly.api.toml", "WARNING")
        elif passed < 3:
            log("🔧 API deployment issues. Check Fly.dev logs", "WARNING")
        elif passed < 5:
            log("🔧 Frontend/Node.js proxy issues. Check configuration", "WARNING")
        else:
            log("🔧 Minor issues. Check CORS or endpoint configuration", "WARNING")
            
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
