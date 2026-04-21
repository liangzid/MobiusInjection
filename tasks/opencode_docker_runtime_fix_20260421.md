# OpenCode Docker Runtime Fix - 2026-04-21

## User request

Dr. Frost asked to cautiously inspect and fix OpenCode-specific evaluation issues:

- OpenCode should run from the correct Docker-side project directory.
- OpenCode skill checks should look in the Docker-side path that OpenCode actually scans.
- The experiment should clarify and improve how the OpenCode container is restored or cleaned.
- Missing base tools in the container should be handled.
- OpenCode output should be preserved even when a run times out.

## Files touched

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
- `experiments/AgentCallInterface/tests/test_opencode_caller.py`
- `tasks/opencode_docker_runtime_fix_20260421.md`

## Findings

- `docker exec opencode pwd` starts in `/`, while OpenCode project-local skills are discovered from the active project directory.
- `opencode run --help` supports `--dir`, and `opencode debug skill` discovers skills under `/opencode/.opencode/skills/<name>/SKILL.md`.
- `/opencode/skills/*.md` and `/opencode/skill/*` are not discovered by OpenCode.
- The `opencode:pre_eval_backup` image starts with `sleep infinity` and without the `/opencode` project directory, which is suitable as a relatively clean base.
- The container was missing `ps`; Debian `apt-get` is present, so `procps` can be installed best-effort before the eval.
- OpenCode does not appear to dynamically load skills created during the same `opencode run` process. After the process exits, a new `opencode run` can see skills that were created in `/opencode/.opencode/skills`.

## Changes made

- OpenCode caller now runs `opencode run --dir /opencode` after `cd /opencode`.
- The caller prepends an environment note telling the agent to create OpenCode skills at `.opencode/skills/<skill-name>/SKILL.md`.
- The caller passes `--dangerously-skip-permissions` for the OpenCode Docker eval flow.
- The caller preserves stdout and stderr, marks known stderr model/API failures as failed, and keeps partial output on timeout.
- The caller tries to clean lingering `opencode run --dir /opencode` processes after timeout.
- The eval script restores `opencode` from the pre-evaluation backup image before the OpenCode run by default.
- The eval script prepares `/opencode`, removes known stale project artifacts, and best-effort installs `procps` when `ps` is missing.
- The eval script captures post-injection OpenCode project tree and `opencode debug skill` output into an agent state file.
- The eval script reports skill artifact and runtime skill discovery in metrics and summary notes.

## Verification

- `bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh` passed.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest experiments/AgentCallInterface/tests/test_opencode_caller.py` passed.
- A Docker OpenCode smoke run showed `/opencode/.opencode/skills/.../SKILL.md` artifacts and `opencode debug skill` registration after the injection process.
- A short timeout smoke test confirmed partial output is returned and stale OpenCode run processes are killed.

## Remaining behavior to account for

- The injection run may still fail or time out if it tries to invoke a skill created earlier in the same OpenCode process, because OpenCode reports available skills from the process-start snapshot.
- The follow-up run starts a new OpenCode process and can discover the created skills, but recursive injected skills can still cause long-running behavior or timeout.
