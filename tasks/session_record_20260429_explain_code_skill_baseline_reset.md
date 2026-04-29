# Session Record: Explain Code Skill Baseline Reset

Date: 2026-04-29

## User Request

Dr. Frost chose `explain-code` as the baseline setting for the skill edit
experiment series. The requested current-stage work was to create a new script
that resets the three Docker agent environments so they have a clean
`explain-code` skill baseline. The pass criterion is that after agent startup,
the agent can load the `explain-code` skill.

The script should be reusable as the future experiment foundation and should
not commit a Docker image after preparation.

## Files Changed

- Added `experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh`
- Added `experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py`
- Added `tasks/session_record_20260429_explain_code_skill_baseline_reset.md`

## Script Behavior

The reset script prepares these project-level skill locations:

- Claude Code:
  `/tmp/claude-code-runs/<CLAUDE_RUN_ID>/workspace/.claude/skills/explain-code/SKILL.md`
- OpenCode:
  `/opencode/.opencode/skills/explain-code/SKILL.md`
- Kilo Code:
  `/kilo_eval_workspace/.kilo/skills/explain-code/SKILL.md`

Defaults:

- `CLAUDE_RUN_ID=explain-code-baseline`
- `AGENTS=claude_code,opencode,kilo_code`
- `VERIFY_AGENT_START=0`

The script cleans project-local skill roots before installing the baseline:

- `.opencode/skills`
- `.agents/skills`
- `.claude/skills`
- `.kilo/skills`
- `.kilocode/skills`

For Claude Code, the script resets only the dedicated run directory and writes
the project-level skill. It intentionally does not install duplicate user-level
or runtime-home copies, because that caused Claude startup to list
`explain-code` twice.

## Baseline Skill

The installed `explain-code` skill is intentionally short and read-only. It asks
the agent to explain code with:

- a plain-language analogy;
- a small ASCII diagram;
- a step-by-step walkthrough;
- one gotcha, edge case, or maintenance risk.

It also instructs the agent not to modify files when the skill is used.

## Commands Run

Syntax and dry-run:

```bash
bash -n experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh
DRY_RUN=1 bash experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh
DRY_RUN=1 VERIFY_AGENT_START=1 bash experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh
```

Tests:

```bash
uv run --no-sync pytest experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py
```

Container reset:

```bash
bash experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh
```

Claude startup probe:

```bash
ANTHROPIC_AUTH_TOKEN="$(tr -d '\n' < privacy_secret_openrouter_API_key.txt)" \
VERIFY_AGENT_START=1 \
AGENTS=claude_code \
VERIFY_TIMEOUT_SECONDS=45 \
bash experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh
```

Discovery checks:

```bash
docker exec opencode bash -lc 'cd /opencode && /root/.opencode/bin/opencode debug skill | grep -E "\"name\": \"(explain-code|integrity-sync|performance-audit)\"" || true'
docker exec kilo_code bash -lc 'cd /kilo_eval_workspace && kilo debug skill | grep -E "\"name\": \"(explain-code|integrity-sync|performance-audit)\"" || true'
docker exec claude_code bash -lc 'grep -F "\"skills\"" /tmp/explain-code-claude-probe.jsonl | tail -1'
```

## Results

- Bash syntax check passed.
- Dry-run passed.
- Dry-run with `VERIFY_AGENT_START=1` passed after fixing a bug where the
  optional OpenCode/Kilo startup probes did not respect dry-run.
- Targeted tests passed: `4 passed`.
- Real reset completed successfully for all three containers.
- OpenCode `debug skill` discovered only `explain-code` among the checked
  baseline/injection skill names.
- Kilo Code `debug skill` discovered only `explain-code` among the checked
  baseline/injection skill names.
- Claude Code startup init listed:
  - `slash_commands`: includes `explain-code`
  - `skills`: includes a single `explain-code`

The first Claude API-backed probe proved a native `Skill` tool call as well,
but failed the script because `--max-turns 1` stopped after the skill launch.
The script was updated to validate Claude startup skill visibility from the init
event instead of requiring the model to complete the final explanation.

## Current Baseline State

The three running Docker containers are prepared for the initial
`explain-code` skill edit experiments:

- `claude_code`
- `opencode`
- `kilo_code`

No Docker image was committed.

## Verification

- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py`
  passed with `4 passed`.
- Real reset script exited with code `0`.
- Claude startup probe exited with code `0` after the init-event validation
  change.
