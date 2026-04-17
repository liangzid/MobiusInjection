# Agent Containers Quick Reference

## List of Containers
```
nanobot, opencode, kilo_code, grok_cli, codex, openclaw, droid, zed, claude_code, zeroclaw, hermes
```

## Quick Commands

### Using the script (recommended)
```bash
# From project root
./Env/agent_containers.sh status

# Open shell in container
./Env/agent_containers.sh exec nanobot
./Env/agent_containers.sh exec hermes

# Run a command
./Env/agent_containers.sh run nanobot nanobot --version
./Env/agent_containers.sh run hermes hermes --version

# View logs
./Env/agent_containers.sh logs hermes

# Start/Stop/Restart
./Env/agent_containers.sh stop nanobot
./Env/agent_containers.sh start nanobot
./Env/agent_containers.sh restart hermes
```

### Direct Docker Commands

```bash
# Enter container shell
docker exec -it nanobot bash          # bash containers
docker exec -it droid sh               # alpine containers

# Run command directly
docker exec nanobot nanobot --version
docker exec hermes bash -c "source ~/.local/bin/env && hermes --version"
docker exec claude_code bash -c 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && claude --version'
```

## Tool-Specific Commands

| Agent | Version Command |
|-------|----------------|
| nanobot | `docker exec nanobot nanobot --version` |
| opencode | `docker exec opencode /root/.opencode/bin/opencode --version` |
| kilo_code | `docker exec kilo_code kilo --version` |
| grok_cli | `docker exec grok_cli grok --version` |
| codex | `docker exec codex codex --version` |
| openclaw | `docker exec openclaw openclaw --version` |
| droid | `docker exec droid droid --version` |
| zed | `docker exec zed zed --version` |
| claude_code | `docker exec claude_code claude --version` |
| zeroclaw | `docker exec zeroclaw /home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw --version` |
| hermes | `docker exec hermes /root/.hermes/hermes-agent/venv/bin/hermes --version` |

## Python API (Recommended)

### Setup

The API key is read from `privacy_secret_openrouter_API_key.txt` in the project root:

```python
from experiments.AgentCallInterface.utils.api_keys import get_openrouter_api_key

api_key = get_openrouter_api_key()  # Reads from privacy file
```

### Basic Usage

```python
from experiments.AgentCallInterface.agents.agent_callers import get_caller, DEFAULT_MODEL

caller = get_caller('nanobot')
response = caller.call({
    'task_id': 'test-001',
    'problem_statement': 'What is 2+2? Answer in one number.'
}, timeout=90)  # Uses DEFAULT_MODEL = 'openrouter/free'
print(f"Success: {response.success}")
print(f"Output: {response.output}")
```

### With Model Override

```python
caller = get_caller('nanobot')

# Use default model (openrouter/free)
response = caller.call(task_input, timeout=90)

# Use specific model
response = caller.call(task_input, timeout=90, model='anthropic/claude-sonnet-4.6')
```

### Default Model

```python
from experiments.AgentCallInterface.agents.agent_callers import DEFAULT_MODEL
print(DEFAULT_MODEL)  # 'openrouter/free'
```

## Verified Agent Calling Formats

| Agent | Docker Exec Command | Default Model | Status |
|-------|-------------------|---------------|--------|
| **nanobot** | `docker exec nanobot nanobot agent -m "prompt" --no-markdown` | `openrouter/free` | ✅ Verified |
| **hermes** | `docker exec hermes bash -c 'export OPENROUTER_API_KEY=... && /root/.hermes/hermes-agent/venv/bin/hermes chat -q "prompt" --provider openrouter'` | `openrouter/free` | ✅ Verified |
| **zeroclaw** | `docker exec zeroclaw /home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw agent -m "prompt"` | `openrouter/free` | ✅ Verified |
| **openclaw** | `docker exec -e OPENROUTER_API_KEY=... openclaw openclaw infer model run --local --model "custom-openrouter-ai/{model}" --prompt "prompt"` | `openrouter/auto` | ✅ Verified |
| **kilo_code** | `docker exec kilo_code kilo run -m {model} --auto "prompt"` | `kilo/openrouter/free` | ✅ Verified |
| **opencode** | `docker exec -e OPENROUTER_API_KEY=... opencode /root/.opencode/bin/opencode run -m {model} "prompt"` | `opencode/big-pickle` | ✅ Verified |
| **codex** | `docker exec -e OPENROUTER_API_KEY=... codex codex exec --full-auto --skip-git-repo-check -c "provider=openrouter" -c "model={model}" "prompt"` | `openrouter/free` | ⚠️ Issue |
| **droid** | `docker exec -e FACTORY_API_KEY=... droid droid exec "prompt"` | N/A | ⚠️ Alpine |
| **zed** | GUI-based editor | N/A | ❌ No CLI |
| **cursor** | GUI-based IDE | N/A | ❌ No CLI |

### Agent-Specific Model Formats

| Agent | Recommended Models | Notes |
|-------|------------------|-------|
| nanobot | `openrouter/free`, `openrouter/auto` | Uses OpenRouter |
| hermes | `openrouter/free`, `openrouter/auto` | Uses OpenRouter |
| zeroclaw | `openrouter/free`, `openrouter/auto` | Uses OpenRouter |
| openclaw | `openrouter/auto`, `anthropic/claude-sonnet-4.6` | Uses `custom-openrouter-ai/{model}` prefix |
| kilo_code | `kilo/openrouter/free` | Uses kilo's model format |
| opencode | `opencode/big-pickle`, `opencode/gpt-5-nano` | Built-in models |
| codex | `openrouter/free`, `qwen/qwen3-coder:free` | OpenRouter via config |

## Agent Configuration Status

### ✅ Configured and Working
All agents read API key from `privacy_secret_openrouter_API_key.txt` via the `api_keys.py` utility:
- **nanobot**: Uses `openrouter/free`
- **hermes**: Uses `openrouter/free`
- **zeroclaw**: Uses `openrouter/free`
- **openclaw**: Uses `openrouter/auto` (via custom provider prefix)
- **kilo_code**: Uses `kilo/openrouter/free`
- **opencode**: Uses `opencode/big-pickle`

### ⚠️ Known Issues
- **codex**: OpenRouter connection works but may have API compatibility issues
- **droid**: Alpine container (uses `sh` not `bash`)

### ❌ No CLI Mode
- **zed**: GUI-based editor, no autonomous CLI
- **cursor**: GUI-based IDE, no autonomous CLI
