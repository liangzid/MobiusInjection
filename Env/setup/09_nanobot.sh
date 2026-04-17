#!/bin/bash
# Nanobot Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/09_nanobot.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# Nanobot API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
export GEMINI_API_KEY="${GEMINI_API_KEY}"
SETUP_EOF

mkdir -p ~/.nanobot

cat > ~/.nanobot/config.json << 'SETUP_EOF'
{
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
SETUP_EOF

echo "Nanobot configured. Reload shell or run: source ~/.bashrc"