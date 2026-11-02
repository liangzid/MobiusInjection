# Claude Code Skill Location Analysis - 2026-04-28

## User Request

Dr. Frost asked whether the main issue is the skill creation location, since
Claude Code skills should theoretically be under `.claude/skills`; how the
current prompt creates skills; why they are placed in the workspace; and where
they should be placed inside Docker so Claude Code loads them correctly.

## Files Checked

- `mobiusInjection/CODING_AGENT_TEMPLATE_V6_LOOP.py`
- `mobiusInjection/CODING_AGENT_TEMPLATE_V3.py`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `papers/attack_surface_analysis.md`
- Existing run evidence from the same-workspace follow-up LIMIT=1 run.

## Findings

- Current V6 prompt routes `claude_code` to skill root `skills`, so it asks the
  agent to create:
  - `skills/integrity-sync/SKILL.md`
  - `skills/performance-audit/SKILL.md`
  - `skills/sync-check-record.jsonl`
- This means the files are created under the Claude workspace ordinary
  directory, not under a Claude native skill discovery directory.
- This behavior was inherited from V3. V3 explicitly says hidden `.claude`
  writes are permission-sensitive for Claude Code, so it preferred the
  project-local root `skills/` and said not to use `.claude`.
- The repo notes list Claude native skill locations as:
  - personal skills: `~/.claude/skills/`
  - project skills: `.claude/skills/`
- The Claude runner does not use the container's normal `/home/zi` as HOME for
  each benchmark call. `ClaudeCodeCaller` creates a per-run directory:
  - run dir: `/tmp/claude-code-runs/<safe_run_id>`
  - runtime HOME: `/tmp/claude-code-runs/<safe_run_id>/home`
  - runtime workspace: `/tmp/claude-code-runs/<safe_run_id>/workspace`
- The command exports `HOME=$CLAUDE_RUNTIME_HOME`, creates `$HOME/.claude`,
  changes directory to `$CLAUDE_WORKSPACE`, and then starts `claude`.
- Therefore, for this harness, the likely native load paths are:
  - user-level: `/tmp/claude-code-runs/<safe_run_id>/home/.claude/skills/<skill>/SKILL.md`
  - project-level: `/tmp/claude-code-runs/<safe_run_id>/workspace/.claude/skills/<skill>/SKILL.md`
- Placing files at `/home/zi/.claude/skills` inside the container is not
  sufficient under this runner unless the runner copies them into the per-run
  `$HOME/.claude/skills`, because `HOME` is overridden before Claude starts.

## Evidence From Latest Follow-Up Test

- The same-workspace follow-up fix worked: main and follow-up ran in the same
  `/tmp/claude-code-runs/<run_id>/workspace`.
- Claude's stream init event still listed only built-in skills:
  `update-config`, `debug`, `simplify`, `batch`, `loop`, and `claude-api`.
- It did not list `integrity-sync` or `performance-audit`.
- The follow-up saw existing trace records but did not append a new native skill
  event, which supports the conclusion that `workspace/skills` was not loaded as
  a native Claude Code skill root.

## Current Conclusion

The primary issue is very likely the Claude Code skill location. The prompt is
creating skill files successfully, but in `workspace/skills`, which is not being
loaded by Claude Code's native skill discovery in this harness.

## Suggested Next Experiment

- Create a V7 prompt or runner-side setup that targets Claude native locations:
  - preferably `$CLAUDE_WORKSPACE/.claude/skills/<skill>/SKILL.md` for project
    skills, and optionally also `$HOME/.claude/skills/<skill>/SKILL.md`.
- Update state capture to include:
  - `workspace/.claude/skills`
  - `home/.claude/skills`
  - ordinary `workspace/skills` for comparison.
- Run LIMIT=1 with Claude Code and verify against Claude stream init:
  - success requires the init `skills` list or slash-skill behavior to show the
    injected skill names, not only manual JSONL trace creation.
- If prompt-side writes to `.claude/skills` are blocked as sensitive config
  writes, preinstall skills in the per-run runtime home/workspace before launching
  Claude Code rather than relying on the agent to create them during the same
  session.
