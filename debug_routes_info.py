#!/usr/bin/env python3
"""
Debug script to analyze routes in FastAPI server code
Since we can't execute Python directly, we'll analyze the code structure
"""

import re

def analyze_fastapi_routes():
    """Analyze routes by reading the server.py file"""
    try:
        with open('cli/server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 ANALYZING FASTAPI ROUTES IN cli/server.py")
        print("=" * 50)
        
        # Find all @app.get, @app.post, etc. decorators
        route_patterns = [
            r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\s*\(\s*"([^"]+)"',
            r"@app\.(get|post|put|delete|patch)\s*\(\s*'([^']+)'"
        ]
        
        found_routes = []
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                found_routes.append((method, path))
        
        if found_routes:
            print("📍 FOUND ROUTES:")
            for method, path in found_routes:
                print(f"   {method} {path}")
        else:
            print("❌ NO ROUTES FOUND - might be using APIRouter")
            
        # Check for APIRouter usage
        if "APIRouter" in content:
            print("\n⚠️  APIRouter detected in code")
            
        if "include_router" in content:
            print("⚠️  include_router detected - might be issue")
        else:
            print("✅ No include_router found - using direct decorators")
            
        # Check for our specific routes
        scraper_start_routes = [route for method, route in found_routes if "/scraper/start" in route]
        if scraper_start_routes:
            print(f"\n✅ SCRAPER START ROUTES FOUND: {len(scraper_start_routes)}")
            for method, path in scraper_start_routes:
                print(f"   {method} {path}")
        else:
            print("\n❌ NO /scraper/start ROUTES FOUND!")
            
        return found_routes
        
    except Exception as e:
        print(f"❌ Error analyzing routes: {e}")
        return []

if __name__ == "__main__":
    routes = analyze_fastapi_routes()
    
    print(f"\n📊 SUMMARY: Found {len(routes)} total routes")
    
    # Check critical routes
    critical_routes = ["/scraper/start", "/api/scraper/start", "/health"]
    print("\n🎯 CRITICAL ROUTES CHECK:")
    for critical in critical_routes:
        found = any(critical in path for method, path in routes)
        status = "✅ FOUND" if found else "❌ MISSING"
        print(f"   {critical}: {status}")
