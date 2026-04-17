#!/bin/bash
# OpenCode Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/03_opencode.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# OpenCode API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export GEMINI_API_KEY="${GEMINI_API_KEY}"
export GROQ_API_KEY="${GROQ_API_KEY}"
SETUP_EOF

cat > ~/.opencode.json << 'SETUP_EOF'
{
  "providers": {
    "openai": {
      "apiKey": "${OPENAI_API_KEY}",
      "disabled": false
    },
    "anthropic": {
      "apiKey": "${ANTHROPIC_API_KEY}",
      "disabled": false
    },
    "openrouter": {
      "apiKey": "${OPENROUTER_API_KEY}",
      "disabled": false
    },
    "groq": {
      "apiKey": "${GROQ_API_KEY}",
      "disabled": false
    }
  },
  "agents": {
    "coder": {
      "model": "claude-3-5-sonnet",
      "maxTokens": 5000
    }
  },
  "autoCompact": true
}
SETUP_EOF

echo "OpenCode configured. Reload shell or run: source ~/.bashrc"