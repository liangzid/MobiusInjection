#!/bin/bash
# Droid Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/10_droid.sh

set -e

cat >> ~/.profile << 'SETUP_EOF'
# Droid API Configuration
export FACTORY_API_KEY="${FACTORY_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

mkdir -p ~/.droid

cat > ~/.droid/config.yml << 'SETUP_EOF'
api:
  provider: "openai"
  model: "gpt-4o"

tools:
  enabled:
    - bash
    - file_read
    - file_write
    - web_search
SETUP_EOF

echo "Droid configured. Reload shell or run: source ~/.profile"