#!/bin/bash
# Deployment script for FastAPI backend to Fly.dev

echo "🚀 DEPLOYING FASTAPI BACKEND TO FLY.DEV"
echo "=" * 50

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in to Fly
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.dev. Please run: fly auth login"
    exit 1
fi

echo "✅ Fly CLI ready"

# Create Fly app if it doesn't exist
echo "📦 Creating/checking Fly app: glow-nest-api"
if ! fly apps list | grep -q "glow-nest-api"; then
    echo "Creating new Fly app..."
    fly apps create glow-nest-api --generate-name false
else
    echo "✅ App glow-nest-api already exists"
fi

# Create volume for database persistence
echo "💾 Creating/checking volume for database..."
if ! fly volumes list -a glow-nest-api | grep -q "glow_nest_data"; then
    echo "Creating volume..."
    fly volumes create glow_nest_data --region fra --size 1 -a glow-nest-api
else
    echo "✅ Volume glow_nest_data already exists"
fi

# Set environment variables
echo "🔧 Setting environment variables..."
fly secrets set -a glow-nest-api \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=8080

# Deploy the application
echo "🚀 Deploying application..."
fly deploy -c fly.api.toml -a glow-nest-api

# Check deployment status
echo "🔍 Checking deployment status..."
fly status -a glow-nest-api

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10  # Wait for deployment to stabilize

API_URL="https://glow-nest-api.fly.dev"
echo "Testing health endpoint: $API_URL/health"

if curl -f -s "$API_URL/health" > /dev/null; then
    echo "✅ Health check passed"
    echo "📊 Health response:"
    curl -s "$API_URL/health" | python -m json.tool 2>/dev/null || curl -s "$API_URL/health"
else
    echo "❌ Health check failed"
    echo "🔧 Check logs with: fly logs -a glow-nest-api"
fi

echo ""
echo "🎯 DEPLOYMENT SUMMARY"
echo "=" * 30
echo "App name: glow-nest-api"
echo "URL: https://glow-nest-api.fly.dev"
echo "Health: $API_URL/health"
echo "Routes: $API_URL/__debug/routes"
echo "Scraper: $API_URL/scraper/start"
echo ""
echo "📋 Next steps:"
echo "1. Run acceptance tests: python test_api_deployment.py"
echo "2. Test from frontend: Use Self-Test button in admin panel"
echo "3. Monitor logs: fly logs -a glow-nest-api"
echo "4. Scale if needed: fly scale count 2 -a glow-nest-api"
