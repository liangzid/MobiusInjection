# Session Record - 2026-04-21 - MiniMax Coding Agents Eval Script

## User Instruction

Create a complete experiment script that uses
`experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh` to run one full
evaluation for OpenCode, Kilo Code, and Claude Code with the MiniMax model.

## Files Touched

- `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh`
- `experiments/AgentCallInterface/tests/test_minimax_eval_script.py`
- `tasks/session_record_20260421_minimax_coding_agents_eval.md`

## Work Performed

1. Added a dedicated wrapper script for the three coding agents.
2. Fixed the v3 coding-agent script preflight check so it checks
   `TEMPLATE_V3.py`, matching the injection template it imports.
3. Added a dry-run mode to the wrapper for fast command/config verification
   without starting Docker/API-backed evaluations.
4. Added pytest coverage for shell syntax and dry-run configuration.

## Verification Performed

### Shell Syntax

- `bash -n experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh`
- `bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`

Results:

- Both shell syntax checks passed.

### Pytest

- `env UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest experiments/AgentCallInterface/tests/test_minimax_eval_script.py`

Results:

- 2 tests passed.

## Internal Results

- Initial `uv run pytest ...` failed because the default uv cache path under
  `/home/zi/.cache/uv` is read-only in the sandbox.
- Retrying with `UV_CACHE_DIR=/tmp/uv-cache` reached dependency resolution, but
  the locked `pyarrow==24.0.0` distribution does not provide a compatible wheel
  for CPython 3.12 in this environment.
- The targeted tests do not need dependency syncing, so verification completed
  with `uv run --no-sync`.
- The wrapper dry-run confirmed that the underlying v3 script will be invoked
  with:
  - model `openrouter/minimax/minimax-m2.5:free`
  - agents `opencode,kilo_code,claude_code`
