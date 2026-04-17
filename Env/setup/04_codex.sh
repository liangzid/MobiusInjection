#!/bin/bash
# Codex Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/04_codex.sh

set -e

cat >> ~/.bashrc << 'SETUP_EOF'
# Codex API Configuration
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
export AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}"
SETUP_EOF

mkdir -p ~/.codex

cat > ~/.codex/config.json << 'SETUP_EOF'
{
  "model": "o4-mini",
  "provider": "openai",
  "providers": {
    "openai": {
      "name": "OpenAI",
      "baseURL": "https://api.openai.com/v1",
      "envKey": "OPENAI_API_KEY"
    },
    "azure": {
      "name": "AzureOpenAI",
      "baseURL": "https://YOUR_PROJECT_NAME.openai.azure.com/openai",
      "envKey": "AZURE_OPENAI_API_KEY"
    },
    "openrouter": {
      "name": "OpenRouter",
      "baseURL": "https://openrouter.ai/api/v1",
      "envKey": "OPENROUTER_API_KEY"
    }
  },
  "history": {
    "maxSize": 1000,
    "saveHistory": true
  }
}
SETUP_EOF

echo "Codex configured. Reload shell or run: source ~/.bashrc"