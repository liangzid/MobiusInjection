#!/bin/bash
# Hermes Agent Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/08_hermes.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# Hermes Agent API Configuration
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
SETUP_EOF

mkdir -p ~/.hermes

cat > ~/.hermes/config.json << 'SETUP_EOF'
{
  "providers": {
    "anthropic": {
      "api_key": "${ANTHROPIC_API_KEY}",
      "base_url": "https://api.anthropic.com"
    },
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "base_url": "https://api.openai.com/v1"
    }
  },
  "default_provider": "anthropic",
  "default_model": "claude-3-5-sonnet"
}
SETUP_EOF

mkdir -p ~/.local/bin
cat > ~/.local/bin/env << 'SETUP_EOF'
#!/bin/bash
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
SETUP_EOF
chmod +x ~/.local/bin/env

echo "Hermes Agent configured. Reload shell or run: source ~/.bashrc"