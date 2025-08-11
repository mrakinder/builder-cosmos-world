#!/usr/bin/env bash
# ULTRA-SAFE DEPLOYMENT - NO AUTO-LAUNCH GUARANTEED
set -euo pipefail

echo "🛡️  ULTRA-SAFE DEPLOYMENT MODE"
echo "🚫 ABSOLUTE NO AUTO-LAUNCH"

# МАКСИМАЛЬНЕ блокування auto-launch
export FLY_NO_LAUNCH=1
export FLY_NO_DEPLOY_LOGS=1
export FLY_NO_BUILDER_CACHE=1
export FLY_FORCE_TOML=1
export FLY_DISABLE_LAUNCH=1

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

echo "🚫 Environment set:"
echo "   FLY_NO_LAUNCH=$FLY_NO_LAUNCH"
echo "   FLY_NO_DEPLOY_LOGS=$FLY_NO_DEPLOY_LOGS"
echo "   FLY_NO_BUILDER_CACHE=$FLY_NO_BUILDER_CACHE"
echo "   FLY_FORCE_TOML=$FLY_FORCE_TOML"
echo "   FLY_DISABLE_LAUNCH=$FLY_DISABLE_LAUNCH"

# ГАРАНТОВАНО видаляємо будь-які auto-generated файли
echo "🧹 Cleaning auto-generated files..."
for f in fly.toml .fly.toml fly.tmp.toml manifest.json .manifest.json; do
  if [ -f "$f" ]; then
    echo "🗑️  Removing: $f"
    rm -f "$f"
  fi
done

# Перевірка нашого конфігу
test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }
grep -q '^app\s*=\s*"' "$CONFIG" || { echo "❌ $CONFIG must contain: app = \"...\""; exit 1; }

echo "📋 Config: $CONFIG"
echo "📋 App: $APP_NAME"

# Показати конфіг
echo "📋 Our config content:"
cat "$CONFIG"
echo ""

# Показати структуру проєкту
echo "📋 Project structure:"
ls -la | head -15
echo ""

# Якщо це frontend - показати package.json build скрипт
if [ "$TARGET" = "frontend" ]; then
  echo "📋 Build script check:"
  grep -A 5 '"build"' package.json || echo "No build script found"
  echo ""
fi

echo "🛫 DEPLOYING WITH ZERO AUTO-DETECTION..."
echo "🚫 NO launch plan generation"
echo "🚫 NO auto-scan"
echo "🚫 NO manifest.json"
echo "🚫 NO auto-generated fly.toml"

# Deploy тільки з нашим explicit config
flyctl deploy --config "$CONFIG" --remote-only --verbose

echo ""
echo "✅ ULTRA-SAFE DEPLOYMENT COMPLETED!"
case "$TARGET" in
  frontend)
    echo "🌐 Frontend: https://glow-nest-frontend.fly.dev"
    ;;
  api)
    echo "🔗 API: https://glow-nest-api.fly.dev"
    ;;
esac
