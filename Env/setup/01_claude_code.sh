#!/bin/bash
# Claude Code Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/01_claude_code.sh

set -e

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

cat >> ~/.bashrc << 'SETUP_EOF'
# Claude Code API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export OPENROUTER_BASE_URL="${OPENROUTER_BASE_URL:-https://openrouter.ai/api}"
SETUP_EOF

mkdir -p ~/.claude/settings

cat > ~/.claude/settings.json << 'SETUP_EOF'
{
  "env": {
    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
    "ANTHROPIC_BASE_URL": "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}",
    "ANTHROPIC_AUTH_TOKEN": "${OPENROUTER_API_KEY}",
    "OPENROUTER_BASE_URL": "${OPENROUTER_BASE_URL:-https://openrouter.ai/api}"
  }
}
SETUP_EOF

echo "Claude Code configured. Reload shell or run: source ~/.bashrc"