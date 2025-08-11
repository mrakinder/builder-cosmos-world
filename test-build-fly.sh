#!/bin/bash

echo "🔧 Testing Fly.io build without deploy..."

# Перенесення старого fly.toml щоб не заважав
if [ -f "fly.toml" ]; then
    echo "📦 Moving old fly.toml to fly.old.toml"
    mv fly.toml fly.old.toml
fi

# Тестування білду на Fly.io без деплою
echo "🔨 Running build test..."
fly deploy --build-only --remote-only --config fly.frontend.toml

if [ $? -eq 0 ]; then
    echo "✅ Build test successful! Ready for deployment."
    echo "🚀 To deploy frontend: fly deploy --config fly.frontend.toml --remote-only"
    echo "🚀 To deploy API: fly deploy --config fly.api.toml --remote-only"
else
    echo "❌ Build test failed"
    exit 1
fi
