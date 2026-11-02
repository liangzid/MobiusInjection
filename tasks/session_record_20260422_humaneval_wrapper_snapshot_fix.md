# HumanEval Wrapper Snapshot Fix Session Record

Date: 2026-04-22

## User Request

Dr. Frost reported that `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
failed at the end of a HumanEval run with:

`line 1213: syntax error near unexpected token 'done'`

The request was to inspect the issue, make a small fix if it was simple, run a
single-task experiment to confirm the error no longer appears, and ask before
changing anything if it turned out to be a complex bug.

## Diagnosis

- `bash -n experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`: passed.
- `bash -n experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`: passed.
- The failed run was:
  `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/humaneval_minimax_benchmark/humaneval_minimax_20260422_154228/wrapper.log`.
- The last case, `HumanEval/9 claude_code`, completed once, then the same case
  unexpectedly entered `TESTING AGENT: claude_code` a second time before failing
  at the final `done`.
- `stat experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh` showed the
  script was modified/touched at `2026-04-22 16:58:39 +0800`, while the wrapper
  was still executing the last case. This matches Bash's known behavior when a
  script file is rewritten while it is still being read by an active shell: the
  parser can lose sync and report a false syntax error later in the file.

## Files Changed

- `experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`
- `experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py`
- `tasks/session_record_20260422_humaneval_wrapper_snapshot_fix.md`

## Implementation

- Added `EVAL_SCRIPT_SNAPSHOT` under each benchmark run directory.
- Added `snapshot_eval_script()` to copy the basic eval script into the run
  directory before executing cases.
- Updated `run_case()` to execute the snapshot instead of the mutable source
  script.
- Added a pytest case confirming that dry-run creates the snapshot and that the
  snapshot content matches the source script.

## Verification

- `bash -n experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`: passed.
- `bash -n experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`: passed.
- `UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest experiments/AgentCallInterface/tests/test_humaneval_benchmark_script.py`: passed, 3 tests.
- `DRY_RUN=1 LIMIT=1 CODING_EVAL_AGENTS=opencode bash experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`: passed and printed the snapshot path.
- Single-task real smoke:
  - Command: `TIMEOUT_SECONDS=60 FOLLOWUP_TIMEOUT_SECONDS=20 LIMIT=1 CODING_EVAL_AGENTS=opencode bash experiments/scripts/1.0.2.run_minimax_humaneval_injection_benchmark.sh`
  - Run directory: `experiments/logs/humaneval_minimax_benchmark/humaneval_minimax_20260422_171030`
  - Result: wrapper reached `Benchmark run complete` and did not reproduce the
    `done` syntax error.
  - Case result: `opencode` timed out after the intentionally shortened 60
    second timeout, so the case was recorded as runner/runtime failure and
    timeout. This is separate from the wrapper control-flow bug.

## Internal Notes

- Existing unrelated worktree changes were left untouched.
- The root cause was not a static syntax error in the current basic eval script;
  it was long-running Bash execution against a mutable script file.
