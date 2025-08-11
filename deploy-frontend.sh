#!/bin/bash

# Деплой фронтенда на Fly.io
set -euo pipefail

# Блокуємо будь-яке auto-launch від Fly
export FLY_NO_LAUNCH=1
# Прибираємо потенційно згенеровані конфіги
rm -f fly.toml .fly.toml fly.tmp.toml 2>/dev/null || true

echo "🚀 Deploying Glow Nest Frontend to Fly.io..."

# Перевірка локальної збірки
echo "📦 Testing local build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Local build successful"
else
    echo "❌ Local build failed"
    exit 1
fi

# Деплой на Fly.io
echo "🛫 Deploying to Fly.io..."
fly deploy --config fly.frontend.toml --remote-only

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Frontend URL: https://glow-nest-frontend.fly.dev"
    echo "🔍 Check status: fly status --app glow-nest-frontend"
    echo "📋 View logs: fly logs --app glow-nest-frontend"
else
    echo "❌ Deployment failed"
    exit 1
fi
