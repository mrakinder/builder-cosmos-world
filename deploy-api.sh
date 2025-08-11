#!/usr/bin/env bash
set -euo pipefail

CONFIG=${CONFIG:-fly.api.toml}
APP_NAME=${APP_NAME:-glow-nest-api}

# 1) sanity checks
test -f "$CONFIG" || { echo "❌ Missing $CONFIG"; exit 1; }
grep -q '^app\s*=\s*"' "$CONFIG" || { echo "❌ $CONFIG must contain: app = \"...\""; exit 1; }

# 2) disable auto-launch
export FLY_NO_LAUNCH=1

# 3) avoid conflicting root fly.toml
if [ -f fly.toml ] && [ "$(basename "$CONFIG")" != "fly.toml" ]; then
  echo "⚠️  Renaming root fly.toml to avoid conflicts"
  mv -f fly.toml fly.old.toml
fi

# 4) build & deploy using explicit config
echo "🚀 Deploying $APP_NAME with $CONFIG"
flyctl deploy --config "$CONFIG" --remote-only
