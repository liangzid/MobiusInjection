# Session Record: Coding Agent Lifecycle Hooks

Date: 2026-04-22

## User Request

Unify the prepare/capture/cleanup lifecycle hooks for Claude Code, OpenCode, and Kilo Code in the coding-agent experiment runner. After implementation, run one real Docker-container plus OpenRouter API e2e test across all three agents.

## Files Changed

- `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
- `experiments/AgentCallInterface/tests/test_coding_eval_script.py`
- `tasks/session_record_20260422_coding_agent_lifecycle_hooks.md`

## Implementation Notes

- Added unified lifecycle entrypoints in the coding eval script:
  - `restore_agent_container`
  - `prepare_agent_container`
  - `capture_agent_state`
  - `cleanup_agent_container`
  - `collect_agent_cleanup_metrics`
  - `append_agent_lifecycle_notes`
- Changed `run_agent_eval` to call the shared lifecycle hooks for every coding agent instead of branching directly on OpenCode/Kilo.
- Added `AGENT_STATE_FILES` tracking so pre, post-injection, and cleanup captures from all agents are passed into `mobius_monitor`.
- Extended lifecycle coverage to Claude Code:
  - prepare cleans `/tmp/claude-code-runs`
  - capture records run-root tree, injected/memory files, and eval subprocesses
  - cleanup removes run-root contents and `/tmp/test_data.txt`
  - cleanup metrics report run-root, subprocess, and tmp-file state
- Preserved OpenCode restarted-session checking after post-injection capture.
- Fixed Claude subprocess cleanup counting to ignore the active capture/count shell itself.

## Tests And Results

- `bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`: passed.
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_coding_eval_monitor_e2e.py experiments/AgentCallInterface/tests/test_mobius_monitor.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: failed before test execution because `pyarrow==24.0.0` has no CPython 3.12 wheel/source distribution for this platform.
- `PYTHONPATH=. pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_coding_eval_monitor_e2e.py experiments/AgentCallInterface/tests/test_mobius_monitor.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: 20 passed.

## Real E2E Run

Command:

```bash
bash experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh
```

First run after initial implementation:

- Eval ID: `basic_coding_eval_20260422_105848`
- Summary: `experiments/logs/basic_coding_eval_20260422_105848_summary.txt`
- Result:
  - OpenCode: `Success`; lifecycle state files and analysis generated.
  - Kilo Code: `Failed`; injection hit the 300s timeout, cleanup metrics were clean.
  - Claude Code: `Success`; cleanup run root was clean, but subprocess count showed a false positive from the active capture shell.

Final run after fixing the Claude false-positive subprocess counter:

- Eval ID: `basic_coding_eval_20260422_111038`
- Summary: `experiments/logs/basic_coding_eval_20260422_111038_summary.txt`
- Result:
  - OpenCode: `Failed`; output reported OpenRouter/provider error `502 Network connection lost` / `provider_unavailable`.
  - Kilo Code: `Success`; cleanup metrics `WorkspaceClean: Yes`, `SubprocessClean: Yes`, `TmpClean: Yes`.
  - Claude Code: `Success`; cleanup metrics `RunRootClean: Yes`, `SubprocessClean: Yes`, `TmpClean: Yes`.

## Internal Result

The unified lifecycle hook path executed end-to-end for all three coding agents. The final OpenCode failure was an upstream provider/network error, not a lifecycle-hook failure. Kilo and Claude completed with clean lifecycle cleanup metrics in the final real e2e run.
