# Agent Containers Usage Guide

This document describes how to use the 11 agent tool containers configured for the Mobius Injection research project.

## Container List

| Container Name | Agent Tool | Base Image | Access Command |
|---------------|------------|------------|----------------|
| nanobot | Nanobot | python:3.11-slim | `docker exec -it nanobot bash` |
| opencode | OpenCode | debian:bookworm-slim | `docker exec -it opencode bash` |
| kilo_code | Kilo Code | node:24-slim | `docker exec -it kilo_code bash` |
| grok_cli | Grok CLI | node:24-slim | `docker exec -it grok_cli bash` |
| codex | Codex | node:24-slim | `docker exec -it codex bash` |
| openclaw | OpenClaw | node:24-slim | `docker exec -it openclaw bash` |
| droid | Droid | alpine:latest | `docker exec -it droid sh` |
| zed | Zed | alpine:latest | `docker exec -it zed sh` |
| claude_code | Claude Code | ubuntu:22.04 | `docker exec -it claude_code bash` |
| zeroclaw | Zeroclaw | ubuntu:22.04 | `docker exec -it zeroclaw bash` |
| hermes | Hermes Agent | ubuntu:22.04 | `docker exec -it hermes bash` |

## Quick Usage

### 1. Enter a Container Shell

```bash
# For bash-based containers
docker exec -it <container_name> bash

# For sh-based containers (alpine)
docker exec -it <container_name> sh
```

Examples:
```bash
docker exec -it nanobot bash
docker exec -it opencode bash
docker exec -it hermes bash
docker exec -it droid sh
```

### 2. Run Commands Directly

```bash
# Run nanobot
docker exec nanobot nanobot --help

# Run opencode
docker exec opencode bash -c "source ~/.bashrc && opencode --version"

# Run kilo code
docker exec kilo_code kilocode --help

# Run grok cli
docker exec grok_cli grok --help

# Run codex
docker exec codex codex --help

# Run openclaw
docker exec openclaw openclaw --version

# Run droid
docker exec droid droid --help

# Run zed
docker exec zed zed --version

# Run claude code
docker exec claude_code bash -c "eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)\" && claude --version"

# Run zeroclaw
docker exec zeroclaw bash -c "eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)\" && zeroclaw --version"

# Run hermes agent
docker exec hermes bash -c "source ~/.local/bin/env && hermes --version"
```

### 3. Mount Project Directory

To access your local project files from within a container:

```bash
docker run --rm -v /home/zi/paper_mobius:/workspace -w /workspace <image> <command>
```

Example:
```bash
docker run --rm -v /home/zi/paper_mobius:/workspace -w /workspace opencode opencode
```

### 4. Persistent Shell Session

```bash
# Start a long-running container (already done)
docker run -d --name myagent ubuntu:22.04 sleep infinity

# Attach to it
docker exec -it myagent bash
```

## Container Maintenance

### Check Container Status
```bash
docker ps --format '{{.Names}}: {{.Status}}'
```

### View Container Logs
```bash
docker logs <container_name>
```

### Restart a Stopped Container
```bash
docker start <container_name>
```

### Stop a Container
```bash
docker stop <container_name>
```

### Remove a Container
```bash
docker rm -f <container_name>
```

## Tool-Specific Notes

### Claude Code & Zeroclaw (Homebrew)
These require Homebrew environment to be loaded:
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"
```

### Hermes Agent
Requires PATH setup:
```bash
source ~/.local/bin/env
```

### OpenCode
Installed at `~/.local/bin/` - may need to source `~/.bashrc` first:
```bash
source ~/.bashrc && opencode --version
```

### Zed
Installed at `~/.local/bin/` - may need PATH addition:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Docker System Cleanup

If disk space is low:
```bash
docker system prune -af
docker volume prune -f
```

## Disk Usage Check
```bash
docker system df
```
