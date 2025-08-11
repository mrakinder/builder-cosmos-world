#!/usr/bin/env bash
set -euo pipefail
export FLY_NO_LAUNCH=1

CONFIG=${CONFIG:-fly.frontend.toml}
APP_NAME=${APP_NAME:-glow-nest-frontend}

test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }
grep -q '^app\s*=\s*"' "$CONFIG" || { echo "❌ $CONFIG must contain: app = \"...\""; exit 1; }

if [ -f fly.toml ] && [ "$(basename "$CONFIG")" != "fly.toml" ]; then
  echo "⚠️  Renaming root fly.toml to avoid conflicts"
  mv -f fly.toml fly.old.toml
fi

echo "🚀 Deploying $APP_NAME with $CONFIG"
flyctl deploy --config "$CONFIG" --remote-only
