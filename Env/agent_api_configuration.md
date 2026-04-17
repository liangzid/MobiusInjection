# Agent LLM API Configuration Guide

This document describes how to configure LLM API keys and endpoints for all 11 agent tools in the Mobius Injection research project.

## Table of Contents
1. [Claude Code](#1-claude-code)
2. [OpenClaw](#2-openclaw)
3. [OpenCode](#3-opencode)
4. [Codex](#4-codex)
5. [Kilo Code](#5-kilo-code)
6. [Grok CLI](#6-grok-cli)
7. [Zeroclaw](#7-zeroclaw)
8. [Hermes Agent](#8-hermes-agent)
9. [Nanobot](#9-nanobot)
10. [Droid](#10-droid)
11. [Zed](#11-zed)
12. [OpenRouter Unified Configuration](#12-openrouter-unified-configuration)

---

## 1. Claude Code

### Configuration File Location
- Linux/Mac: `~/.claude/settings.json`
- Windows: `%USERPROFILE%\.claude\settings.json`

### Basic Configuration
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
    "ANTHROPIC_BASE_URL": "https://api.anthropic.com"
  }
}
```

### Using Third-Party API Providers

#### Using OpenRouter (Recommended for China)
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-or-v1-your-openrouter-key",
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api"
  }
}
```

#### Using Chinese API Providers
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
    "ANTHROPIC_API_KEY": "your-api-key"
  }
}
```

### Environment Variables (Alternative)
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### Container Usage
```bash
docker exec claude_code bash -c 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && claude'
```

### Key Models Supported
- claude-opus-4
- claude-sonnet-4.6
- claude-3-5-sonnet
- claude-3-5-haiku

---

## 2. OpenClaw

### Configuration File Location
- Linux/Mac: `~/.openclaw/openclaw.json`

### Configuration Structure
```json
{
  "meta": {
    "lastTouchedVersion": "2026.x.x",
    "lastTouchedAt": "2026-01-01T00:00:00.000Z"
  },
  "models": {
    "mode": "merge",
    "providers": {
      "openai": {
        "apiKey": "your-openai-key",
        "baseURL": "https://api.openai.com/v1"
      },
      "anthropic": {
        "apiKey": "your-anthropic-key",
        "baseURL": "https://api.anthropic.com"
      },
      "openrouter": {
        "apiKey": "sk-or-v1-your-key",
        "baseURL": "https://openrouter.ai/api/v1"
      }
    },
    "default": "claude-3-5-sonnet"
  },
  "auth": {
    "profiles": {
      "anthropic:default": {
        "provider": "anthropic",
        "mode": "api_key"
      }
    }
  }
}
```

### Adding Custom Provider (Example: OpenRouter)
```bash
openclaw configure --section model
# Follow interactive prompts
```

### Manual Configuration
Edit `~/.openclaw/openclaw.json`:
```json
{
  "models": {
    "providers": {
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": "sk-or-v1-your-key",
        "api": "openai-completions",
        "models": [
          {
            "id": "anthropic/claude-opus-4",
            "name": "Claude Opus 4",
            "contextWindow": 200000
          }
        ]
      }
    }
  }
}
```

### Container Usage
```bash
docker exec -it openclaw bash
# Inside container:
openclaw configure
```

### Key Models Supported
- OpenAI: GPT-4, GPT-4o, o1, o3
- Anthropic: Claude Opus 4, Claude Sonnet 4.6, Claude 3.5
- Google: Gemini 2.5, Gemini 2.0 Flash
- OpenRouter: 200+ models

---

## 3. OpenCode

### Note
OpenCode has been archived and continued as **Crush** (by Charm team). The container has OpenCode v1.4.x installed.

### Configuration File Location
- `~/.opencode.json` (user home)
- `./.opencode.json` (project local)

### Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export OPENAI_API_KEY="sk-your-key"
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export GEMINI_API_KEY="your-gemini-key"
export GROQ_API_KEY="your-groq-key"
```

### Configuration File (`~/.opencode.json`)
```json
{
  "providers": {
    "openai": {
      "apiKey": "your-api-key",
      "disabled": false
    },
    "anthropic": {
      "apiKey": "your-api-key",
      "disabled": false
    },
    "openrouter": {
      "apiKey": "sk-or-v1-your-key",
      "disabled": false
    },
    "groq": {
      "apiKey": "your-groq-key",
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
```

### Container Usage
```bash
docker exec -it opencode bash
# Inside container:
source ~/.bashrc
opencode
```

### Key Models Supported
- OpenAI: GPT-4.1, GPT-4o, O1, O3 family
- Anthropic: Claude 4 Opus/Sonnet, Claude 3.5
- GitHub Copilot models
- Google Gemini 2.5
- Groq: Llama 4, Deepseek R1

---

## 4. Codex

### Configuration File Location
- `~/.codex/config.json` or `~/.codex/config.yaml`

### Configuration File (`~/.codex/config.json`)
```json
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
```

### Environment Variables
```bash
export OPENAI_API_KEY="sk-your-key"
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export AZURE_OPENAI_API_KEY="your-azure-key"
```

### Container Usage
```bash
docker exec -it codex bash
# Inside container:
codex --help
```

### Key Commands
- `/init` - Initialize project with AGENTS.md
- `/compact` - Summarize and compact conversation

---

## 5. Kilo Code

### Configuration
Kilo Code is a VS Code/IDE extension. Configuration is typically done through:
1. VS Code Settings UI
2. Project-local `.kilocode` configuration

### Key Settings
```json
{
  "kilocode.claudeApiKey": "your-api-key",
  "kilocode.claudeModel": "claude-3-5-sonnet",
  "kilocode.claudeEndpoint": "https://api.anthropic.com"
}
```

### Container Usage
Since Kilo Code is primarily a VS Code extension, the container has the CLI installed:
```bash
docker exec kilo_code kilocode --help
```

### CLI Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export OPENAI_API_KEY="sk-your-key"
```

---

## 6. Grok CLI

### Configuration
Grok CLI uses environment variables for API configuration.

### Environment Variables
```bash
export GROK_API_KEY="your-grok-api-key"
# Or using xAI API directly
export XAI_API_KEY="your-xai-key"
```

### Container Usage
```bash
docker exec -it grok_cli bash
# Inside container:
grok --version
```

### Provider Configuration
Grok CLI supports multiple providers:
```bash
# Using Groq (open source models)
export GROQ_API_KEY="your-groq-key"

# Using OpenRouter
export OPENROUTER_API_KEY="sk-or-v1-your-key"
```

---

## 7. Zeroclaw

### Configuration File Location
- `~/.zeroclaw/config.toml`

### Configuration Example
```toml
[models]
default = "claude-3-5-sonnet"

[models.providers.anthropic]
api_key = "sk-ant-your-key"
base_url = "https://api.anthropic.com"

[models.providers.openai]
api_key = "sk-your-key"
base_url = "https://api.openai.com/v1"

[models.providers.openrouter]
api_key = "sk-or-v1-your-key"
base_url = "https://openrouter.ai/api/v1"

[auth]
# Authentication configuration

[workspace]
path = "~/.zeroclaw/workspace"
```

### Container Usage
```bash
docker exec -it zeroclaw bash
# Inside container:
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"
zeroclaw --version
zeroclaw status
zeroclaw agent -m "Your question"
```

### Key Features
- Single binary, very lightweight
- Supports multiple model providers
- Rust-native implementation

---

## 8. Hermes Agent

### Configuration Location
- `~/.hermes/` directory
- `~/.hermes/hermes-agent` (installation directory)
- `~/.hermes/skills/` (user-created skills)

### Environment Setup
```bash
# Load Hermes environment
source ~/.local/bin/env
```

### API Configuration
Hermes Agent uses environment variables for LLM providers:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export OPENAI_API_KEY="sk-your-key"
export OPENROUTER_API_KEY="sk-or-v1-your-key"

# Or using a custom endpoint
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

### Provider Configuration File
Create `~/.hermes/config.json`:
```json
{
  "providers": {
    "anthropic": {
      "api_key": "sk-ant-your-key",
      "base_url": "https://api.anthropic.com"
    },
    "openai": {
      "api_key": "sk-your-key",
      "base_url": "https://api.openai.com/v1"
    }
  },
  "default_provider": "anthropic",
  "default_model": "claude-3-5-sonnet"
}
```

### Container Usage
```bash
docker exec -it hermes bash
# Inside container:
source ~/.local/bin/env
hermes --version
hermes agent
```

### Unique Features
- Self-evolving: learns from experience and creates skills
- Persistent memory across sessions
- MCP (Model Context Protocol) support

---

## 9. Nanobot

### Configuration
Nanobot (nanobot-ai pip package) uses environment variables:

### Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export OPENAI_API_KEY="sk-your-key"
export OPENROUTER_API_KEY="sk-or-v1-your-key"

# For specific providers
export DEEPSEEK_API_KEY="your-deepseek-key"
export GEMINI_API_KEY="your-gemini-key"
```

### MCP Server Configuration
Nanobot supports MCP servers. Configure in `~/.nanobot/config.json`:
```json
{
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    }
  }
}
```

### Container Usage
```bash
docker exec -it nanobot bash
# Inside container:
nanobot --help
nanobot agent "Your task here"
```

### Key Supported Channels
- Telegram
- Discord
- WhatsApp
- Web
- Terminal

---

## 10. Droid

### Configuration
Droid (Factory AI CLI) uses environment variables:

### Environment Variables
```bash
export FACTORY_API_KEY="your-factory-api-key"
export OPENAI_API_KEY="sk-your-key"
```

### Configuration File
`~/.droid/config.yml`:
```yaml
api:
  provider: "openai"
  model: "gpt-4o"

tools:
  enabled:
    - bash
    - file_read
    - file_write
    - web_search
```

### Container Usage
```bash
docker exec -it droid sh
# Inside container:
droid --help
```

---

## 11. Zed

### Note
Zed is primarily a code editor with AI features. In the container, the `zed` CLI is installed for agentic features.

### Configuration
Zed AI configuration is typically in `~/.config/zed/settings.json`:

```json
{
  "AI": {
    "provider": "anthropic",
    "api_key": "sk-ant-your-key",
    "model": "claude-3-5-sonnet"
  }
}
```

### Using Zed AI Features
```bash
docker exec -it zed bash
# Inside container:
export PATH="$HOME/.local/bin:$PATH"
zed --version
```

### Zed AI Agent Mode
Zed has introduced "Agentic Editing" - allows AI to autonomously write and execute code.

---

## 12. OpenRouter Unified Configuration

OpenRouter is recommended as a unified API gateway for all agents since it:
- Provides single API key for 200+ models
- Supports OpenAI-compatible format
- Automatic failover and model selection
- Works in China with appropriate configuration

### Getting Started with OpenRouter

1. **Register**: https://openrouter.ai
2. **Get API Key**: Dashboard → Keys → Create
3. **Fund Account**: Add credits (minimum $1-5 for testing)

### OpenRouter Models for Coding

| Model | Use Case | Price |
|-------|----------|-------|
| anthropic/claude-opus-4 | Complex architecture, deep reasoning | High |
| anthropic/claude-sonnet-4.6 | Daily coding, balanced | Medium |
| google/gemini-2.5-pro | Long context, multimodal | Medium |
| openai/gpt-4o | General coding | Medium |
| deepseek/deepseek-v3 | Cost-effective | Low |
| meta-llama/llama-4-maverick | Fast inference | Low |

### Unified OpenRouter Setup for All Agents

```bash
# Set once, use everywhere
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

---

## Quick Reference: Container API Setup Commands

### One-Time Setup Script
```bash
#!/bin/bash
# setup_apis.sh - Run inside each container

# Claude Code / Zeroclaw (Homebrew containers)
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"
export ANTHROPIC_API_KEY="sk-ant-your-key"
export OPENROUTER_API_KEY="sk-or-v1-your-key"

# Test
claude --version  # or
zeroclaw --version
```

### Per-Container Environment File
Create `~/.env` in each container:
```
ANTHROPIC_API_KEY=sk-ant-your-key
OPENROUTER_API_KEY=sk-or-v1-your-key
ANTHROPIC_BASE_URL=https://openrouter.ai/api
```

---

## Troubleshooting

### "No API key found" Error
1. Verify environment variable is set: `echo $ANTHROPIC_API_KEY`
2. Check config file syntax (JSON must be valid)
3. Restart the agent after configuration

### Authentication Failed
1. Verify API key is correct and active
2. Check if key has sufficient credits
3. Verify base URL is correct for the provider

### Container Environment
For persistent API configuration in containers:
```bash
# Add to ~/.bashrc or ~/.profile in container
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```
