# Agent Containers Quick Reference

## List of Containers
```
nanobot, opencode, kilo_code, grok_cli, codex, openclaw, droid, zed, claude_code, zeroclaw, hermes
```

## Quick Commands

### Using the script (recommended)
```bash
# From project root
./scripts/agent_containers.sh status

# Open shell in container
./scripts/agent_containers.sh exec nanobot
./scripts/agent_containers.sh exec hermes

# Run a command
./scripts/agent_containers.sh run nanobot nanobot --version
./scripts/agent_containers.sh run hermes hermes --version

# View logs
./scripts/agent_containers.sh logs hermes

# Start/Stop/Restart
./scripts/agent_containers.sh stop nanobot
./scripts/agent_containers.sh start nanobot
./scripts/agent_containers.sh restart hermes
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
| nanobot | `nanobot --version` |
| opencode | `bash -c "source ~/.bashrc && opencode --version"` |
| kilo_code | `kilocode --version` |
| grok_cli | `grok --version` |
| codex | `codex --version` |
| openclaw | `openclaw --version` |
| droid | `droid --version` |
| zed | `export PATH="$HOME/.local/bin:$PATH" && zed --version` |
| claude_code | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && claude --version` |
| zeroclaw | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && zeroclaw --version` |
| hermes | `bash -c "source ~/.local/bin/env && hermes --version"` |
