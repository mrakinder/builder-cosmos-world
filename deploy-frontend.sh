#!/bin/bash

# Деплой фронтенда на Fly.io
set -e

echo "🚀 Deploying Glow Nest Frontend to Fly.io..."

# Перевірка локальної збірки
echo "📦 Testing local build..."
npm run build:client

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
