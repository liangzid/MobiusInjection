## Task

- User asked to inspect an OpenClaw Docker image/container to identify the real OpenClaw configuration path.

## Image Inspected

- `openclaw:mobius_eval_config_fixed_20260421`

## Commands Run

- `docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | rg '^openclaw:'`
- `docker run --rm --entrypoint bash openclaw:mobius_eval_config_fixed_20260421 -lc '...'`

## Findings

- Runtime/config root:
  - `/root/.openclaw-mobius-eval`
- Main config file:
  - `/root/.openclaw-mobius-eval/openclaw.json`
- Config audit log:
  - `/root/.openclaw-mobius-eval/logs/config-audit.jsonl`
- Session registry:
  - `/root/.openclaw-mobius-eval/agents/main/sessions/sessions.json`
- Session JSONL files:
  - `/root/.openclaw-mobius-eval/agents/main/sessions/*.jsonl`
- Workspace dir recorded by the session state:
  - `/root/.openclaw/workspace-mobius-eval`

- Bundled skill root actually referenced by the session snapshot:
  - `/usr/local/lib/node_modules/openclaw/skills`

## Evidence

- `openclaw.json` exists under `/root/.openclaw-mobius-eval`.
- `config-audit.jsonl` records writes to `/root/.openclaw-mobius-eval/openclaw.json`.
- `sessions.json` includes `resolvedSkills` entries such as:
  - `/usr/local/lib/node_modules/openclaw/skills/healthcheck/SKILL.md`
  - `/usr/local/lib/node_modules/openclaw/skills/node-connect/SKILL.md`
  - `/usr/local/lib/node_modules/openclaw/skills/skill-creator/SKILL.md`
- `sessions.json` also records:
  - `workspaceDir: /root/.openclaw/workspace-mobius-eval`

## Interpretation

- `/root/.openclaw-mobius-eval` is the OpenClaw runtime state/configuration root.
- `/usr/local/lib/node_modules/openclaw/skills` is the native bundled skill root that appears in the loaded skill snapshot.
- These are different layers:
  - config/state under `.openclaw-mobius-eval`
  - bundled skills under `/usr/local/lib/node_modules/openclaw/skills`
