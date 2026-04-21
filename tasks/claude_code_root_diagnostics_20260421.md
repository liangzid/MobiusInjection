# Claude Code Root Diagnostics - 2026-04-21

## User Request

Dr. Frost asked to investigate and reproduce why Claude Code reports that root cannot run Claude under the current configuration, without modifying code.

## Files Reviewed

- `Env/agent_containers_usage.md`
- `Env/agent_containers_quickref.md`
- `Env/agent_api_configuration.md`
- `Env/setup/01_claude_code.sh`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `tasks/docker_agent_cli_diagnostics_20260421.md`

## Commands and Observations

- `docker ps -a --format '{{.Names}} {{.Image}} {{.Status}}'`
  - `claude_code` is running from `claude_code:injected_weak_001`.
- `docker inspect claude_code --format '{{json .Config.User}} ...'`
  - `Config.User` is empty, so Docker runs exec commands as the image/container default user.
- `docker exec claude_code whoami` and `docker exec claude_code id`
  - The default exec user is `root`, UID/GID `0`.
- `docker exec claude_code bash -lc 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"; command -v claude; claude --version'`
  - Claude resolves to `/home/linuxbrew/.linuxbrew/bin/claude`.
  - Version is `2.1.92 (Claude Code)`.
  - Version check succeeds under root.
- `docker exec claude_code bash -lc 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"; claude -p "Say OK only."'`
  - Does not show the root/sudo error first.
  - Fails on malformed URL from current settings: `"${ANTHROPIC_BASE_URL:-https://api.anthropic.com}/v1/messages?beta=true" cannot be parsed as a URL.`
- `docker exec claude_code bash -lc 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"; claude --dangerously-skip-permissions -p "Say OK only."'`
  - Reproduces the target error immediately:
    `--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons`
- `uv run python -c 'from experiments.AgentCallInterface.agents.agent_callers import get_caller; ...'`
  - The project `ClaudeCodeCaller` path returns `success=False`, `returncode=1`, and the same stderr.
- `docker exec -u nobody claude_code ... claude --dangerously-skip-permissions -p "Say OK only."`
  - Does not emit the root/sudo error, confirming UID 0 is the trigger for that specific check.

## Internal Result

The immediate root error is caused by the combination of:

1. The container has no configured non-root runtime user (`Config.User` is empty).
2. `docker exec claude_code ...` therefore runs as root by default.
3. `ClaudeCodeCaller` currently invokes `claude --dangerously-skip-permissions -p "$1"`.
4. Claude Code blocks `--dangerously-skip-permissions` when the process has root/sudo privileges.

This is not because Docker itself runs "as sudo" inside the container. It is Docker's default container user behavior: if the image/container does not specify a `USER`, processes run as UID 0. Host-side permission to talk to the Docker daemon is separate from the UID used for the process inside the container.

There is also a separate current-configuration issue in `/root/.claude/settings.json`: `Env/setup/01_claude_code.sh` writes shell parameter expansions inside a single-quoted heredoc, so the settings file contains literal values like `${ANTHROPIC_BASE_URL:-https://api.anthropic.com}`. When running without `--dangerously-skip-permissions`, Claude reaches API setup and fails because that literal string is not a valid URL.

## Code Changes

No code files were modified. This diagnostic note was added as the required execution record.

## Follow-up Runtime Fix Test

Dr. Frost then asked to correct the independent settings issue and try `docker exec` with a non-root user or permission change.

### Runtime Configuration Change

- Backed up the running container file:
  - `/root/.claude/settings.json.bak-root-diagnostics-20260421`
- Replaced `/root/.claude/settings.json` in the running `claude_code` container with actual URL strings:
  - `ANTHROPIC_BASE_URL = "https://openrouter.ai/api"`
  - `OPENROUTER_BASE_URL = "https://openrouter.ai/api"`
- Did not write the OpenRouter key into the settings file. For tests, the key was passed via `docker exec -e ANTHROPIC_AUTH_TOKEN=...`.

### Follow-up Observations

- The `:-` shell expansion form was not itself the problem. It is valid shell syntax, but it had been written literally into JSON by the single-quoted heredoc in `Env/setup/01_claude_code.sh`.
- After writing a real URL into settings, root mode without bypass no longer fails on URL parsing. It reaches OpenRouter and returns model/auth availability errors for unavailable Claude models.
- Root mode with bypass permissions still fails immediately:
  - `claude --permission-mode bypassPermissions -p ...`
  - `claude --allow-dangerously-skip-permissions --permission-mode bypassPermissions -p ...`
  - Both return `--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons`.
- Non-root mode with `docker exec -u nobody` and `HOME=/tmp/claude-nobody-home` no longer triggers the root/sudo error:
  - `user=nobody uid=65534 home=/tmp/claude-nobody-home`
  - `claude --dangerously-skip-permissions -p ...` proceeds to API/model handling.
- Explicit Claude-family models tested through OpenRouter returned region errors:
  - `claude-sonnet-4-6`
  - `anthropic/claude-sonnet-4.5`
- OpenRouter free/non-Claude model names completed at the CLI/API level with return code 0 but an empty `result` field:
  - `nvidia/nemotron-3-super-120b-a12b:free`
  - `openrouter/free`

### Updated Internal Result

The root/sudo blocker is specifically tied to Claude Code's bypass-permission mode. Running as a non-root user is enough to get past that blocker. Running as root is also possible only if bypass permission mode is not used.

The next remaining issue is model/provider compatibility: with the current OpenRouter key and location, Claude-family models are rejected by region policy, while OpenRouter free model aliases complete but return an empty final `result` through Claude Code's Anthropic-compatible path.

## Implemented Non-root Runtime Fix

Dr. Frost asked to apply the non-root runtime design first, defer deeper model compatibility testing, and verify that Docker can start the experiment flow.

### Repository Changes

- Updated `Env/setup/01_claude_code.sh`.
  - Ensures a container-local `zi` user exists.
  - Initializes `/home/zi/.claude/settings.json` with concrete OpenRouter-compatible URL strings.
  - Avoids writing API keys into the settings file.
  - Avoids writing literal shell expansion expressions into JSON.
- Updated `experiments/AgentCallInterface/agents/agent_callers.py`.
  - `ClaudeCodeCaller` now runs `docker exec -u zi`.
  - Each task gets an isolated runtime home and workspace under `/tmp/claude-code-runs/<safe-run-id>/`.
  - Claude Code receives `HOME`, `CLAUDE_RUNTIME_HOME`, `CLAUDE_WORKSPACE`, OpenRouter base URLs, auth token, and model as environment variables.
  - The per-run home copies `/home/zi/.claude/settings.json` as a template if needed.
- Updated `experiments/AgentCallInterface/tests/test_agent_callers.py`.
  - Added assertions for non-root Docker execution, isolated HOME/workspace paths, model/key env injection, and safe run id normalization.

### Runtime Container Update

- Copied the updated setup script into the running `claude_code` container as `/tmp/setup_agent.sh`.
- Ran `docker exec claude_code bash /tmp/setup_agent.sh`.
- Verified:
  - `zi:x:1000:1000::/home/zi:/bin/bash`
  - `uid=1000(zi) gid=1000(zi)`
  - `/home/zi/.claude/settings.json` contains concrete URL strings.
  - `docker exec -u zi -e HOME=/home/zi claude_code ... claude --version` returns `2.1.92 (Claude Code)`.

### Verification

- `bash -n Env/setup/01_claude_code.sh`
  - Passed.
- `uv run pytest experiments/AgentCallInterface/tests/test_agent_callers.py -q`
  - Passed: `11 passed`.
- Ran `ClaudeCodeCaller` through Docker with model `nvidia/nemotron-3-super-120b-a12b:free`.
  - `success=True`
  - `returncode=0`
  - no stderr
  - no root/sudo error
  - no malformed URL error
- Verified the runtime paths created by the caller:
  - `/tmp/claude-code-runs/claude_nonroot_smoke/home`
  - `/tmp/claude-code-runs/claude_nonroot_smoke/workspace`
  - owned by `zi:zi`
  - Claude state files were created inside that run-specific home.

### Remaining Issue

The Docker and non-root Claude Code startup path is now working. The tested OpenRouter free/open-source model path still returned an empty stdout from Claude Code, so model/output compatibility remains a separate follow-up item.
