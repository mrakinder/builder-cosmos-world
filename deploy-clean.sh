#!/usr/bin/env bash
# Clean deployment script - NO AUTO-LAUNCH
set -euo pipefail

# CRITICAL: Block all auto-launch mechanisms
export FLY_NO_LAUNCH=1
export FLY_NO_DEPLOY_LOGS=1
export FLY_NO_BUILDER_CACHE=1

TARGET=${1:-frontend}

echo "🚀 Clean deployment with NO auto-launch"
echo "Target: $TARGET"

# Remove any conflicting fly.toml from root
if [ -f fly.toml ]; then
  echo "⚠️  Found root fly.toml - moving to fly.old.toml"
  mv fly.toml fly.old.toml
fi

case "$TARGET" in
  frontend)
    CONFIG="fly.frontend.toml"
    APP_NAME="glow-nest-frontend"
    ;;
  api)
    CONFIG="fly.api.toml"
    APP_NAME="glow-nest-api"
    ;;
  *)
    echo "❌ Usage: $0 [frontend|api]"
    exit 1
    ;;
esac

# Validate config exists
test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }

# Validate app name format
grep -q '^app\s*=\s*"' "$CONFIG" || { 
  echo "❌ $CONFIG must contain: app = \"...\""; 
  exit 1; 
}

echo "📋 Config: $CONFIG"
echo "📋 App: $APP_NAME"
echo "📋 NO auto-launch: FLY_NO_LAUNCH=$FLY_NO_LAUNCH"

# Clean deployment - ONLY explicit config
echo "🛫 Deploying with explicit config only..."
flyctl deploy --config "$CONFIG" --remote-only

echo "✅ Deployment completed!"
case "$TARGET" in
  frontend)
    echo "🌐 Frontend: https://glow-nest-frontend.fly.dev"
    ;;
  api)
    echo "🔗 API: https://glow-nest-api.fly.dev"
    ;;
esac
