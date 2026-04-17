#!/bin/bash
# Kilo Code Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/05_kilo_code.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# Kilo Code API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

mkdir -p ~/.kilocode

cat > ~/.kilocode/config.json << 'SETUP_EOF'
{
  "claudeApiKey": "${ANTHROPIC_API_KEY}",
  "claudeModel": "claude-3-5-sonnet",
  "claudeEndpoint": "https://api.anthropic.com"
}
SETUP_EOF

echo "Kilo Code configured. Reload shell or run: source ~/.bashrc"