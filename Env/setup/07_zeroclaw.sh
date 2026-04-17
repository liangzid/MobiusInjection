#!/bin/bash
# Zeroclaw Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/07_zeroclaw.sh

set -e

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

cat >> ~/.bashrc << 'SETUP_EOF'
# Zeroclaw API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

mkdir -p ~/.zeroclaw

cat > ~/.zeroclaw/config.toml << 'SETUP_EOF'
[models]
default = "claude-3-5-sonnet"

[models.providers.anthropic]
api_key = "${ANTHROPIC_API_KEY}"
base_url = "https://api.anthropic.com"

[models.providers.openai]
api_key = "${OPENAI_API_KEY}"
base_url = "https://api.openai.com/v1"

[models.providers.openrouter]
api_key = "${OPENROUTER_API_KEY}"
base_url = "https://openrouter.ai/api/v1"

[auth]

[workspace]
path = "~/.zeroclaw/workspace"
SETUP_EOF

echo "Zeroclaw configured. Reload shell or run: source ~/.bashrc"