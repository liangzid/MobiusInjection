# OpenRouter Free Models Configuration Guide

This document describes how to configure each agent to use OpenRouter with free models.

## Verified Free Models on OpenRouter

The following models have been verified as completely free (pricing = $0):

| Model ID | Description | Context Window |
|----------|-------------|----------------|
| `qwen/qwen3-coder:free` | **Qwen3 Coder 480B** - Specialized for coding | 262K |
| `google/gemma-3-27b-it:free` | Google Gemma 3 27B Instruct | 131K |
| `google/gemma-3-12b-it:free` | Google Gemma 3 12B Instruct | 32K |
| `meta-llama/llama-3.2-3b-instruct:free` | Meta Llama 3.2 3B | 131K |
| `google/gemma-3-4b-it:free` | Google Gemma 3 4B | 32K |
| `openrouter/elephant-alpha` | Elephant Alpha (100B) | 256K |
| `z-ai/glm-4.5-air:free` | Z.ai GLM 4.5 Air | 131K |

**Recommended for Coding**: `qwen/qwen3-coder:free` (480B model specialized for code generation)

## Agent Configuration Guide

**Default Free Model**: `qwen/qwen3-coder:free`

---

### 1. Claude Code

**Configuration File**: `~/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "YOUR_OPENROUTER_API_KEY",
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
    "OPENROUTER_API_KEY": "YOUR_OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1"
  }
}
```

**Setup Command**:
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"
export ANTHROPIC_AUTH_TOKEN="YOUR_OPENROUTER_API_KEY"
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
```

---

### 2. OpenClaw

**Configuration File**: `~/.openclaw/openclaw.json`

```json
{
  "meta": {
    "lastTouchedVersion": "2026.x.x",
    "lastTouchedAt": "2026-04-17T00:00:00.000Z"
  },
  "models": {
    "mode": "merge",
    "providers": {
      "openrouter": {
        "apiKey": "YOUR_OPENROUTER_API_KEY",
        "baseURL": "https://openrouter.ai/api/v1"
      }
    },
    "default": "qwen/qwen3-coder:free"
  },
  "auth": {
    "profiles": {
      "openrouter:free": {
        "provider": "openrouter",
        "mode": "api_key"
      }
    }
  }
}
```

---

### 3. OpenCode

**Configuration File**: `~/.opencode.json`

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "YOUR_OPENROUTER_API_KEY",
      "disabled": false
    }
  },
  "agents": {
    "coder": {
      "model": "qwen/qwen3-coder:free",
      "maxTokens": 5000
    }
  },
  "autoCompact": true
}
```

---

### 4. Codex

**Configuration File**: `~/.codex/config.json`

```json
{
  "model": "qwen/qwen3-coder:free",
  "provider": "openrouter",
  "providers": {
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
```

---

### 5. Kilo Code

**Configuration File**: `~/.kilocode/config.json`

```json
{
  "openrouterApiKey": "YOUR_OPENROUTER_API_KEY",
  "openrouterModel": "qwen/qwen3-coder:free"
}
```

---

### 6. Grok CLI

Grok CLI uses environment variables. For OpenRouter:

```bash
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
```

---

### 7. Zeroclaw

**Configuration File**: `~/.zeroclaw/config.toml`

```toml
[models]
default = "qwen/qwen3-coder:free"

[models.providers.openrouter]
api_key = "YOUR_OPENROUTER_API_KEY"
base_url = "https://openrouter.ai/api/v1"

[auth]

[workspace]
path = "~/.zeroclaw/workspace"
```

---

### 8. Hermes Agent

**Configuration File**: `~/.hermes/config.json`

```json
{
  "providers": {
    "openrouter": {
      "api_key": "YOUR_OPENROUTER_API_KEY",
      "base_url": "https://openrouter.ai/api/v1"
    }
  },
  "default_provider": "openrouter",
  "default_model": "qwen/qwen3-coder:free"
}
```

---

### 9. Nanobot

Nanobot uses environment variables. For OpenRouter:

```bash
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
```

---

### 10. Droid

**Configuration File**: `~/.droid/config.yml`

```yaml
api:
  provider: "openrouter"
  model: "qwen/qwen3-coder:free"

tools:
  enabled:
    - bash
    - file_read
    - file_write
    - web_search
```

---

### 11. Zed

**Configuration File**: `~/.config/zed/settings.json`

```json
{
  "AI": {
    "provider": "openrouter",
    "api_key": "YOUR_OPENROUTER_API_KEY",
    "model": "qwen/qwen3-coder:free"
  }
}
```

---

## All Verified Free Models

Complete list of free models (retrieved from OpenRouter API):

```
openrouter/elephant-alpha - Elephant (ctx:262144)
google/gemma-4-26b-a4b-it:free - Google Gemma 4 26B A4B (ctx:262144)
google/gemma-4-31b-it:free - Google Gemma 4 31B (ctx:262144)
nvidia/nemotron-3-super-120b-a12b:free - NVIDIA Nemotron 3 Super (ctx:262144)
minimax/minimax-m2.5:free - MiniMax M2.5 (ctx:196608)
arcee-ai/trinity-large-preview:free - Arcee Trinity Large (ctx:131000)
liquid/lfm-2.5-1.2b-thinking:free - LiquidAI LFM2.5-1.2B-Thinking (ctx:32768)
liquid/lfm-2.5-1.2b-instruct:free - LiquidAI LFM2.5-1.2B-Instruct (ctx:32768)
nvidia/nemotron-3-nano-30b-a3b:free - NVIDIA Nemotron 3 Nano 30B A3B (ctx:256000)
nvidia/nemotron-nano-12b-v2-vl:free - NVIDIA Nemotron Nano 12B 2 VL (ctx:128000)
qwen/qwen3-next-80b-a3b-instruct:free - Qwen3 Next 80B A3B (ctx:262144)
nvidia/nemotron-nano-9b-v2:free - NVIDIA Nemotron Nano 9B V2 (ctx:128000)
openai/gpt-oss-120b:free - OpenAI gpt-oss-120b (ctx:131072)
openai/gpt-oss-20b:free - OpenAI gpt-oss-20b (ctx:131072)
z-ai/glm-4.5-air:free - Z.ai GLM 4.5 Air (ctx:131072)
qwen/qwen3-coder:free - Qwen3 Coder 480B A35B (ctx:262000) **RECOMMENDED**
cognitivecomputations/dolphin-mistral-24b-venice-edition:free - Venice Uncensored (ctx:32768)
google/gemma-3n-e2b-it:free - Google Gemma 3n 2B (ctx:8192)
google/gemma-3n-e4b-it:free - Google Gemma 3n 4B (ctx:8192)
meta-llama/llama-guard-4-12b:free - Meta Llama Guard 4 12B (ctx:163840)
google/gemma-3-4b-it:free - Google Gemma 3 4B (ctx:32768)
google/gemma-3-12b-it:free - Google Gemma 3 12B (ctx:32768)
google/gemma-3-27b-it:free - Google Gemma 3 27B (ctx:131072)
meta-llama/llama-3.3-70b-instruct:free - Meta Llama 3.3 70B (ctx:65536)
meta-llama/llama-3.2-3b-instruct:free - Meta Llama 3.2 3B (ctx:131072)
nousresearch/hermes-3-llama-3.1-405b:free - Nous Hermes 3 405B (ctx:131072)
```

## Verification

After configuration, verify each agent can access OpenRouter:

```bash
# Test OpenClaw
docker exec openclaw bash -c 'cat ~/.openclaw/openclaw.json'

# Test OpenCode
docker exec opencode bash -c 'cat ~/.opencode.json'

# Test Claude Code
docker exec claude_code bash -c 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && cat ~/.claude/settings.json'
```
