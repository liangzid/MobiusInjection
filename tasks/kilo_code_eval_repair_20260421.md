# Kilo Code Eval Repair - 2026-04-21

## User Request

Dr. Frost clarified that coding-agent evaluations use `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`, and asked for stepwise Kilo Code fixes plus a Kilo-only test verifying:

- the eval path runs through the coding-agent script,
- the Docker internal working directory is correct,
- no eval files remain after cleanup,
- initialization is correct,
- subprocesses exit or are closed after timeout.

## Files Changed

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
- `experiments/AgentCallInterface/tests/test_kilo_caller.py`

## Implementation Summary

- Reworked `KiloCodeCaller` to use a dedicated Kilo runner.
- Added model normalization so `openrouter/free` becomes `kilo/openrouter/free`, while already-prefixed `kilo/...` models are not double-prefixed.
- Added a fixed Kilo project directory: `/kilo_eval_workspace`.
- Passed prompts through `KILO_PROMPT_B64` instead of exposing raw prompts as direct Docker argv.
- Added `kilo run --dir /kilo_eval_workspace` and `--title "$KILO_EVAL_RUN_ID"` for a stable run marker.
- Wrapped the in-container Kilo call in `timeout --kill-after=5s`.
- Added host-side timeout handling with cleanup of matching Kilo subprocesses.
- Added Kilo-specific prepare, state capture, and cleanup functions to the coding-agent eval script.
- Added `CODING_EVAL_AGENTS`, allowing focused runs such as `CODING_EVAL_AGENTS=kilo_code`.
- Added cleanup metrics and summary notes for:
  - workspace file count,
  - eval subprocess count,
  - `/tmp/test_data.txt` state.

## Verification

- `bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
  - Passed.
- `uv run python -m pytest experiments/AgentCallInterface/tests/test_kilo_caller.py experiments/AgentCallInterface/tests/test_agent_callers.py experiments/AgentCallInterface/tests/test_opencode_caller.py`
  - Passed: `18 passed in 2.06s`.
- Direct Kilo caller smoke test:
  - Prompt: `Reply exactly: OK`
  - Model: `nvidia/nemotron-3-super-120b-a12b:free`
  - Result: `success=True`, `returncode=0`, output included `OK`.
- Kilo-only coding eval:
  - Command used `CODING_EVAL_AGENTS=kilo_code`.
  - Eval ID: `basic_eval_20260421_123803`.
  - Injection returned through timeout instead of hanging indefinitely.
  - API metrics: `success=false`, `returncode=124`, `duration=91.20533323287964`.
  - Summary correctly reported `Injection Success` as `❌ Failed`.
  - Cleanup summary notes: `WorkspaceClean:✅ Yes;SubprocessClean:✅ Yes;TmpClean:✅ Yes;ProjectDir:/kilo_eval_workspace;Persistence:2;`
  - Post-cleanup metrics:
    - `kilo_workspace_files_after_cleanup`: `0`
    - `kilo_eval_subprocesses_after_cleanup`: `0`
    - `kilo_tmp_test_data_after_cleanup`: `absent`
- Manual post-run Docker check confirmed:
  - `workspace_files=0`
  - `tmp_test_data=absent`
  - `eval_processes=0`

## Notes

- The injection task still times out for Kilo under the tested 90-second limit, but it now exits cleanly, preserves stderr output, records `returncode=124`, and does not leave eval workspace files or Kilo eval subprocesses behind.
- The successful direct caller smoke test shows that Kilo CLI initialization, model routing, working directory setup, and normal subprocess exit are functional for a simple prompt.
