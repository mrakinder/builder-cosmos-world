#!/usr/bin/env bash
# EXTREME NO AUTO-LAUNCH DEPLOYMENT
set -euo pipefail

echo "🚫 EXTREME NO AUTO-LAUNCH MODE"

# MAXIMAL auto-launch blocking
export FLY_NO_LAUNCH=1
export FLY_NO_DEPLOY_LOGS=1
export FLY_NO_BUILDER_CACHE=1
export FLY_FORCE_TOML=1

TARGET=${1:-frontend}

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

echo "🚫 Environment variables set:"
echo "   FLY_NO_LAUNCH=$FLY_NO_LAUNCH"
echo "   FLY_NO_DEPLOY_LOGS=$FLY_NO_DEPLOY_LOGS"
echo "   FLY_NO_BUILDER_CACHE=$FLY_NO_BUILDER_CACHE"
echo "   FLY_FORCE_TOML=$FLY_FORCE_TOML"

# Remove ANY potential auto-generated fly.toml
for f in fly.toml .fly.toml fly.tmp.toml; do
  if [ -f "$f" ]; then
    echo "⚠️  Removing auto-generated: $f"
    rm -f "$f"
  fi
done

# Validate our explicit config
test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }
grep -q '^app\s*=\s*"' "$CONFIG" || { echo "❌ $CONFIG must contain: app = \"...\""; exit 1; }

echo "📋 Target: $TARGET"
echo "📋 Config: $CONFIG"
echo "📋 App: $APP_NAME"

# Show what's in our config
echo "📋 Config content:"
head -10 "$CONFIG"
echo ""

echo "🛫 Deploying with ZERO auto-detection..."
echo "🚫 NO launch plan generation"
echo "🚫 NO auto-scan"
echo "🚫 NO manifest.json"

# Deploy with explicit config ONLY
flyctl deploy --config "$CONFIG" --remote-only --verbose

echo "✅ Deployment completed with NO auto-launch!"
case "$TARGET" in
  frontend)
    echo "🌐 Frontend: https://glow-nest-frontend.fly.dev"
    ;;
  api)
    echo "🔗 API: https://glow-nest-api.fly.dev"
    ;;
esac
