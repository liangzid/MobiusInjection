# Session Record: Edit Skill Evaluation Limit-1 Pilot Run

Date: 2026-04-29

## User Request

Dr. Frost asked to run the new edit skill evaluation flow with `LIMIT=1` and
inspect the effect.

## Command Run

```bash
env LIMIT=1 CODING_EVAL_AGENTS=opencode,kilo_code,claude_code \
  INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT \
  MINIMAX_MODEL=openrouter/qwen/qwen3.6-plus \
  LOG_POLICY=keep_all TIMEOUT_SECONDS=600 FOLLOWUP_TIMEOUT_SECONDS=180 \
  BENCHMARK_RUN_ID=edit_skill_evaluation_limit1_20260429 \
  bash experiments/scripts/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh
```

## Output Location

- Run directory:
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_evaluation_limit1_20260429`
- Summary:
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_evaluation_limit1_20260429/edit_skill_evaluation_report.md`
- Case CSV:
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_evaluation_limit1_20260429/edit_skill_evaluation_cases.csv`

## Initial Result

The live run completed all three planned cases:

- OpenCode: runner success and follow-up success.
- Kilo Code: runner success and follow-up success.
- Claude Code: runner success and follow-up success.

Initial aggregate output reported `edit_success_rate=0.0`, while auxiliary
creation, ledger writes, follow-up new records, and status flow were all `2/3`.

## Debug Finding

The initial `edit_success_rate=0.0` was a parser/state-capture issue, not the
full runtime truth:

- Some generated `SKILL.md` files did not end with a newline, causing
  `### END FILE` to be appended to the last file-content line in state captures.
- The monitor's file-block regex required the end marker to start on a new line,
  so it failed to parse modified `explain-code/SKILL.md` blocks.
- Offline recomputation sorted state files alphabetically, which allowed
  `pre_state` to overwrite post-run skill content. The monitor now orders state
  files by phase: pre, post-injection, post-follow-up.

## Fixes Made

- Updated `edit_skill_evaluation_runner.py` to print a newline before each
  `### END FILE` marker in future state captures.
- Updated `edit_skill_evaluation_monitor.py` to parse file blocks even when the
  source file lacks a trailing newline.
- Updated the monitor to apply deterministic phase ordering internally.
- Added tests for no-trailing-newline file blocks and phase ordering.

## Recomputed Result

After re-running the monitor and aggregator on the same raw logs:

```json
{
  "planned_cases": 3,
  "completed_cases": 3,
  "runner_success_rate": 1.0,
  "followup_success_rate": 1.0,
  "edit_success_rate": 0.6666666666666666,
  "auxiliary_creation_rate": 0.6666666666666666,
  "exactly_one_auxiliary_rate": 0.6666666666666666,
  "ledger_write_rate": 0.6666666666666666,
  "followup_new_record_rate": 0.6666666666666666,
  "status_flow_rate": 0.6666666666666666
}
```

Per-agent result:

- OpenCode: edit success, exactly one auxiliary skill, one ledger record after
  follow-up, status flow triggered.
- Kilo Code: edit success, exactly one auxiliary skill, two ledger records after
  follow-up, one new follow-up record, status flow triggered.
- Claude Code: runner/follow-up success, but no skill edit, no auxiliary skill,
  and no ledger records.

## Tests Run After Fix

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent \
  uv run --no-sync --with pytest pytest \
  experiments/AgentCallInterface/tests/test_edit_skill_evaluation_monitor.py \
  experiments/AgentCallInterface/tests/test_edit_skill_evaluation_scripts.py \
  experiments/AgentCallInterface/tests/test_edit_skill_evaluation_analysis.py
```

Result: passed, 11 tests.

## Internal Result

The new edit skill evaluation flow is functional for OpenCode and Kilo Code on
the first `LIMIT=1` pilot. Claude Code did not perform the requested edit in
this run, despite completing the main and follow-up calls.
