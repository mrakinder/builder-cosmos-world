#!/usr/bin/env bash
set -euo pipefail

# ЖОРСТКЕ блокування auto-launch
export FLY_NO_LAUNCH=1
export FLY_NO_DEPLOY_LOGS=1

CONFIG=${CONFIG:-fly.frontend.toml}

echo "🚫 NO AUTO-LAUNCH: FLY_NO_LAUNCH=$FLY_NO_LAUNCH"

# прибираємо кореневий fly.toml, якщо заважає
if [ -f fly.toml ] && [ "$(basename "$CONFIG")" != "fly.toml" ]; then
  echo "⚠️  Renaming root fly.toml to avoid conflicts"
  mv -f fly.toml fly.old.toml
fi

# Перевірки
test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }
grep -q '^app\s*=\s*"' "$CONFIG" || { echo "❌ $CONFIG must contain: app = \"...\""; exit 1; }

echo "🚀 Deploying with explicit config: $CONFIG"
echo "📋 NO launch plan generation, NO auto-scan"

flyctl deploy --config "$CONFIG" --remote-only
