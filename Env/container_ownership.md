# Docker Container Ownership

This document identifies which Docker containers belong to Zi Liang (zi) for the Mobius Injection research project.

## Containers Owned by Zi Liang

The following 11 containers are verified to be owned by Zi Liang for agent security research:

| Container Name | Agent Tool | Base Image | Status |
|----------------|------------|------------|--------|
| nanobot | Nanobot | python:3.11-slim | Up 29 hours |
| opencode | OpenCode | debian:bookworm-slim | Up 29 hours |
| kilo_code | Kilo Code | node:24-slim | Up 29 hours |
| grok_cli | Grok CLI | node:24-slim | Up 29 hours |
| codex | Codex | node:24-slim | Up 29 hours |
| openclaw | OpenClaw | node:24-slim | Up 29 hours |
| droid | Droid | alpine:latest | Up 29 hours |
| zed | Zed | alpine:latest | Up 29 hours |
| claude_code | Claude Code | ubuntu:22.04 | Up 29 hours |
| zeroclaw | Zeroclaw | ubuntu:22.04 | Up 29 hours |
| hermes | Hermes Agent | ubuntu:22.04 | Up 29 hours |

## Unidentified Containers

The following containers were found on the GPU server but are **NOT owned by Zi Liang**:

| Container Name | Image | Created | Status | Notes |
|----------------|-------|---------|--------|-------|
| attack_eval__0 | mobile_world:v1.1 | 2026-04-11 | Up 5 hours | Likely belongs to another researcher. Image naming convention differs from user's containers. Created before Mobius Injection project files (Apr 17-18). |

**Action Required**: Do NOT use `attack_eval__0` for experiments. Confirm ownership with labmates if needed.

## Other Containers (Likely Different Researchers)

| Container Name | Image | Status | Notes |
|----------------|-------|--------|-------|
| mobile_world_env_wja_test_avd14t_0 | mobile_world:v1.1 | Up 17 hours | Android emulation environment |
| mobile_world_env_wja_test_0 | mobile_world:v1.1 | Exited (137) | Same image family |
| dialog_test_0 | mobile_world:v1.1 | Up 3 days | Same image family |

## Identification Criteria

Containers were identified as belonging to Zi Liang based on:
1. Consistent naming convention (single underscore: `claude_code`, `zeroclaw`, etc.)
2. Matching documentation in `agent_containers_quickref.md` and `agent_containers_usage.md`
3. Image names correspond to documented agent tools
4. Creation dates align with project timeline (after Apr 17, 2026)

Containers NOT belonging to Zi Liang were identified by:
1. Different naming convention (double underscore: `attack_eval__0`)
2. Unrelated image names (`mobile_world:v1.1` vs agent framework images)
3. Creation dates prior to project initialization

## Last Updated

2026-04-18
