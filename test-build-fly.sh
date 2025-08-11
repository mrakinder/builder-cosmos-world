#!/bin/bash

echo "🔧 Testing Fly.io build without deploy..."

# Тестування білду на Fly.io без деплою
fly deploy --build-only --remote-only --config fly.frontend.toml

if [ $? -eq 0 ]; then
    echo "✅ Build test successful! Ready for deployment."
    echo "🚀 To deploy run: fly deploy --config fly.frontend.toml --remote-only"
else
    echo "❌ Build test failed"
    exit 1
fi
