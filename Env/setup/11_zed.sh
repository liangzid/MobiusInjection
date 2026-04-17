#!/bin/bash
# Zed Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/11_zed.sh

set -e

cat >> ~/.profile << 'SETUP_EOF'
# Zed AI API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export PATH="$HOME/.local/bin:$PATH"
SETUP_EOF

mkdir -p ~/.config/zed

cat > ~/.config/zed/settings.json << 'SETUP_EOF'
{
  "AI": {
    "provider": "anthropic",
    "api_key": "${ANTHROPIC_API_KEY}",
    "model": "claude-3-5-sonnet"
  }
}
SETUP_EOF

echo "Zed configured. Reload shell or run: source ~/.profile"