#!/bin/bash
# Runtime Diagnostics Test Script
# Run this after starting FastAPI backend

echo "🔧 RUNTIME DIAGNOSTICS TESTS"
echo "=" * 50

# Check if FastAPI is running
echo "📡 Checking if FastAPI backend is running..."
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ FastAPI backend is running"
else
    echo "❌ FastAPI backend is not running or not accessible on port 8080"
    echo "Please start it with: python cli/server.py"
    exit 1
fi

echo ""
echo "🧪 TEST 1: Health Check"
echo "-" * 30
echo "Command: curl -sS http://localhost:8080/health"
echo "Response:"
curl -sS http://localhost:8080/health | python -m json.tool 2>/dev/null || curl -sS http://localhost:8080/health
echo ""

echo "🧪 TEST 2: Routes Verification"  
echo "-" * 30
echo "Command: curl -sS http://localhost:8080/__debug/routes"
echo "Response:"
curl -sS http://localhost:8080/__debug/routes | python -m json.tool 2>/dev/null || curl -sS http://localhost:8080/__debug/routes
echo ""

echo "🧪 TEST 3: Scraper Start (Dry Run)"
echo "-" * 30
echo "Command: curl -X POST http://localhost:8080/scraper/start -H Content-Type:application/json -d {...}"
echo "Response:"
curl -X POST http://localhost:8080/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"sale","max_pages":1,"delay_ms":1000,"headful":false}' | python -m json.tool 2>/dev/null || \
curl -X POST http://localhost:8080/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"sale","max_pages":1,"delay_ms":1000,"headful":false}'
echo ""

echo "🧪 TEST 4: API Alias Route"
echo "-" * 30  
echo "Command: curl -X POST http://localhost:8080/api/scraper/start -H Content-Type:application/json -d {...}"
echo "Response:"
curl -X POST http://localhost:8080/api/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"rent","max_pages":1,"delay_ms":1000,"headful":false}' | python -m json.tool 2>/dev/null || \
curl -X POST http://localhost:8080/api/scraper/start \
     -H "Content-Type: application/json" \
     -d '{"listing_type":"rent","max_pages":1,"delay_ms":1000,"headful":false}'
echo ""

echo "🧪 TEST 5: 404 Error Handling"
echo "-" * 30
echo "Command: curl -sS http://localhost:8080/nonexistent/endpoint"
echo "Response:"
curl -sS http://localhost:8080/nonexistent/endpoint | python -m json.tool 2>/dev/null || curl -sS http://localhost:8080/nonexistent/endpoint
echo ""

echo "🎯 SUMMARY"
echo "=" * 50
echo "All tests completed. Check responses above:"
echo "✅ Health should return: {\"ok\": true, \"pid\": ..., \"version\": \"...\"}"
echo "✅ Routes should show: scraper_start: true, api_scraper_start: true"  
echo "✅ Scraper start should return: {\"ok\": true, \"task\": \"...\", \"status\": \"running\"}"
echo "✅ 404 should return JSON: {\"ok\": false, \"error\": \"404 Not Found\", \"path\": \"...\"}"
