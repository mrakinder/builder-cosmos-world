#!/usr/bin/env python3
"""
System Integration Test for Glow Nest XGB 5-Module System
Quick verification that all components are working correctly
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any


class SystemTester:
    """Test all 5 modules and system integration"""
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🧪 Starting Glow Nest XGB System Integration Tests")
        print("=" * 60)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("Database Connectivity", self.test_database),
            ("System Status", self.test_system_status),
            ("Module 1: Scraper API", self.test_scraper_api),
            ("Module 2: ML API", self.test_ml_api),
            ("Module 3: Prophet API", self.test_prophet_api),
            ("Module 4: Streamlit Control", self.test_streamlit_api),
            ("Module 5: Superset Status", self.test_superset_api),
            ("Street Management", self.test_street_management),
            ("Event System", self.test_event_system),
            ("Real-time Features", self.test_realtime_features)
        ]
        
        passed = 0
        total = len(tests)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            for test_name, test_func in tests:
                print(f"\n🔍 Testing: {test_name}")
                try:
                    result = await test_func()
                    if result:
                        print(f"✅ {test_name}: PASSED")
                        passed += 1
                    else:
                        print(f"❌ {test_name}: FAILED")
                        
                    self.test_results[test_name] = result
                    
                except Exception as e:
                    print(f"❌ {test_name}: ERROR - {str(e)}")
                    self.test_results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 60)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! System is ready for production.")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Check the issues above.")
            return False
    
    async def test_api_health(self) -> bool:
        """Test API server health"""
        try:
            async with self.session.get(f"{self.api_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   API Version: {data.get('version', 'unknown')}")
                    return True
                return False
        except:
            print("   ❌ API server not responding")
            return False
    
    async def test_database(self) -> bool:
        """Test database connectivity"""
        try:
            async with self.session.get(f"{self.api_url}/properties/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   Database contains {data.get('total_properties', 0)} properties")
                    return True
                return False
        except:
            return False
    
    async def test_system_status(self) -> bool:
        """Test system status endpoint"""
        try:
            async with self.session.get(f"{self.api_url}/system/status") as response:
                if response.status == 200:
                    data = await response.json()
                    modules = len([k for k in data.keys() if k not in ['active_tasks', 'timestamp', 'database']])
                    print(f"   System tracking {modules} modules")
                    return True
                return False
        except:
            return False
    
    async def test_scraper_api(self) -> bool:
        """Test scraper API endpoints"""
        try:
            # Test status endpoint
            async with self.session.get(f"{self.api_url}/scraper/status") as response:
                if response.status == 200:
                    print("   Scraper API responding")
                    return True
                return False
        except:
            return False
    
    async def test_ml_api(self) -> bool:
        """Test ML API endpoints"""
        try:
            # Test ML status
            async with self.session.get(f"{self.api_url}/ml/status") as response:
                if response.status == 200:
                    data = await response.json()
                    model_exists = data.get('model_exists', False)
                    print(f"   ML Model trained: {model_exists}")
                    return True
                return False
        except:
            return False
    
    async def test_prophet_api(self) -> bool:
        """Test Prophet API endpoints"""
        try:
            # Test Prophet status
            async with self.session.get(f"{self.api_url}/prophet/status") as response:
                if response.status == 200:
                    print("   Prophet API responding")
                    return True
                return False
        except:
            return False
    
    async def test_streamlit_api(self) -> bool:
        """Test Streamlit control API"""
        try:
            # Test Streamlit status
            async with self.session.get(f"{self.api_url}/streamlit/status") as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('status', 'unknown')
                    print(f"   Streamlit status: {status}")
                    return True
                return False
        except:
            return False
    
    async def test_superset_api(self) -> bool:
        """Test Superset API endpoints"""
        try:
            # Test Superset status
            async with self.session.get(f"{self.api_url}/superset/status") as response:
                if response.status == 200:
                    data = await response.json()
                    dashboards = len(data.get('dashboards', []))
                    print(f"   Superset has {dashboards} dashboards available")
                    return True
                return False
        except:
            return False
    
    async def test_street_management(self) -> bool:
        """Test street management API"""
        try:
            # Test get street mappings
            async with self.session.get(f"{self.api_url}/streets/mapping") as response:
                if response.status == 200:
                    data = await response.json()
                    streets = len(data.get('street_mappings', {}))
                    print(f"   Street mappings: {streets} streets configured")
                    return True
                return False
        except:
            return False
    
    async def test_event_system(self) -> bool:
        """Test event logging system"""
        try:
            # Test recent events
            async with self.session.get(f"{self.api_url}/events/recent?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    events = len(data.get('events', []))
                    print(f"   Event system has {events} recent events")
                    return True
                return False
        except:
            return False
    
    async def test_realtime_features(self) -> bool:
        """Test real-time features (simplified)"""
        try:
            # Test if SSE endpoints are accessible
            async with self.session.get(f"{self.api_url}/ml/progress") as response:
                if response.status == 200:
                    print("   Real-time progress tracking available")
                    return True
                return False
        except:
            return False
    
    def generate_report(self):
        """Generate test report"""
        print("\n📋 DETAILED TEST REPORT")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if not self.test_results.get("API Health Check", False):
            print("   • Start the API server: python cli/server.py")
        
        if not self.test_results.get("Database Connectivity", False):
            print("   • Initialize database: python -c \"from cli.utils import ensure_database_schema; ensure_database_schema()\"")
        
        if not self.test_results.get("Module 2: ML API", False):
            print("   • Train ML model through admin panel or API")
        
        print("\n🚀 NEXT STEPS:")
        print("   1. Fix any failed tests above")
        print("   2. Open admin panel: http://localhost:8080/admin/panel/")
        print("   3. Start data collection and model training")
        print("   4. Launch public Streamlit interface")


async def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    else:
        api_url = "http://localhost:8080"
    
    print(f"🎯 Testing Glow Nest XGB system at: {api_url}")
    
    tester = SystemTester(api_url)
    success = await tester.run_all_tests()
    
    # Generate detailed report
    tester.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
