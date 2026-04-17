#!/bin/bash
# Grok CLI Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/06_grok_cli.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# Grok CLI API Configuration
export GROK_API_KEY="${GROK_API_KEY}"
export XAI_API_KEY="${XAI_API_KEY}"
export GROQ_API_KEY="${GROQ_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

echo "Grok CLI configured. Reload shell or run: source ~/.bashrc"