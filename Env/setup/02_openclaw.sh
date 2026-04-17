#!/bin/bash
# OpenClaw Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/02_openclaw.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# OpenClaw API Configuration
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

mkdir -p ~/.openclaw

cat > ~/.openclaw/openclaw.json << 'SETUP_EOF'
{
  "meta": {
    "lastTouchedVersion": "2026.x.x",
    "lastTouchedAt": "2026-04-17T00:00:00.000Z"
  },
  "models": {
    "mode": "merge",
    "providers": {
      "openai": {
        "apiKey": "${OPENAI_API_KEY}",
        "baseURL": "https://api.openai.com/v1"
      },
      "anthropic": {
        "apiKey": "${ANTHROPIC_API_KEY}",
        "baseURL": "https://api.anthropic.com"
      },
      "openrouter": {
        "apiKey": "${OPENROUTER_API_KEY}",
        "baseURL": "https://openrouter.ai/api/v1"
      }
    },
    "default": "claude-3-5-sonnet"
  },
  "auth": {
    "profiles": {
      "anthropic:default": {
        "provider": "anthropic",
        "mode": "api_key"
      }
    }
  }
}
SETUP_EOF

echo "OpenClaw configured. Reload shell or run: source ~/.bashrc"