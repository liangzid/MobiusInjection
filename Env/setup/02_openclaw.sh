#!/bin/bash
# OpenClaw Container Setup Script
# Location: /home/zi/paper_mobius/scripts/setup/02_openclaw.sh

set -euo pipefail

: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY is required for OpenClaw setup}"

cat >> ~/.bashrc << 'SETUP_EOF'
# OpenClaw API Configuration
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
SETUP_EOF

PROFILE_DIR="$HOME/.openclaw-mobius-eval"
AGENT_DIR="$PROFILE_DIR/agents/main/agent"
mkdir -p "$AGENT_DIR"

node << 'SETUP_EOF'
const fs = require("fs");
const os = require("os");
const path = require("path");

const profileDir = path.join(os.homedir(), ".openclaw-mobius-eval");
const agentDir = path.join(profileDir, "agents/main/agent");
const model = "openrouter/nvidia/nemotron-3-super-120b-a12b:free";
const openRouterKey = process.env.OPENROUTER_API_KEY;

const config = {
  gateway: {
    mode: "local",
    auth: { mode: "token", token: "mobius-eval-local-token" },
    tailscale: {},
    controlUi: {
      allowedOrigins: ["http://localhost:18789", "http://127.0.0.1:18789"],
    },
  },
  meta: {
    lastTouchedVersion: "2026.4.15",
    lastTouchedAt: new Date().toISOString(),
  },
  agents: {
    defaults: {
      model: { primary: model },
      models: {
        "openrouter/free": {},
        "openrouter/qwen/qwen3-coder:free": {},
        [model]: {},
      },
    },
  },
  plugins: { entries: { openrouter: { enabled: true } } },
  auth: {
    profiles: {
      "openrouter:manual": { provider: "openrouter", mode: "api_key" },
    },
    order: { openrouter: ["openrouter:manual"] },
  },
};

const authProfiles = {
  profiles: {
    "openrouter:manual": {
      provider: "openrouter",
      type: "api_key",
      key: openRouterKey,
    },
  },
  order: { openrouter: ["openrouter:manual"] },
};

const modelsPath = path.join(agentDir, "models.json");
let models = { providers: {} };
if (fs.existsSync(modelsPath)) {
  models = JSON.parse(fs.readFileSync(modelsPath, "utf8"));
}
models.providers ||= {};
models.providers.openrouter ||= {};
models.providers.openrouter.baseUrl = "https://openrouter.ai/api/v1";
models.providers.openrouter.api = "openai-completions";
models.providers.openrouter.apiKey = "OPENROUTER_API_KEY";
models.providers.openrouter.models ||= [];
const providerModelId = model.replace(/^openrouter\//, "");
if (!models.providers.openrouter.models.some((entry) => entry.id === providerModelId)) {
  models.providers.openrouter.models.push({
    id: providerModelId,
    name: "NVIDIA Nemotron 3 Super 120B A12B (free)",
    reasoning: true,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 131072,
    maxTokens: 8192,
  });
}

fs.writeFileSync(path.join(profileDir, "openclaw.json"), JSON.stringify(config, null, 2) + "\n");
fs.writeFileSync(path.join(agentDir, "auth-profiles.json"), JSON.stringify(authProfiles, null, 2) + "\n");
fs.writeFileSync(modelsPath, JSON.stringify(models, null, 2) + "\n");
SETUP_EOF

chmod 700 "$PROFILE_DIR" "$AGENT_DIR"
chmod 600 "$PROFILE_DIR/openclaw.json" "$AGENT_DIR/auth-profiles.json" "$AGENT_DIR/models.json"

openclaw --profile mobius-eval config validate --json
openclaw --profile mobius-eval models status --plain

echo "OpenClaw mobius-eval profile configured."
