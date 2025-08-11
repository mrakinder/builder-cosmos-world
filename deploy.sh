#!/usr/bin/env bash
set -euo pipefail

# Master deployment script for Glow Nest
# Usage: ./deploy.sh [frontend|api|both]

TARGET=${1:-frontend}

case "$TARGET" in
  frontend)
    echo "🚀 Deploying Frontend..."
    CONFIG=fly.frontend.toml APP_NAME=glow-nest-frontend ./test-build-fly.sh
    ;;
  api)
    echo "🚀 Deploying API..."
    CONFIG=fly.api.toml APP_NAME=glow-nest-api ./deploy-api.sh
    ;;
  both)
    echo "🚀 Deploying both Frontend and API..."
    echo "📦 Deploying API first..."
    CONFIG=fly.api.toml APP_NAME=glow-nest-api ./deploy-api.sh
    echo ""
    echo "📦 Deploying Frontend..."
    CONFIG=fly.frontend.toml APP_NAME=glow-nest-frontend ./test-build-fly.sh
    ;;
  *)
    echo "❌ Usage: $0 [frontend|api|both]"
    exit 1
    ;;
esac

echo ""
echo "✅ Deployment completed!"
echo "🌐 Frontend: https://glow-nest-frontend.fly.dev"
echo "🔗 API: https://glow-nest-api.fly.dev"
