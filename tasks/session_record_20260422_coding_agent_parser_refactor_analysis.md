# Session Record: Coding Agent Parser Refactor Analysis

Date: 2026-04-22

User request:
- Analyze OpenCode and Kilo Code special cases in the coding-agent evaluation script.
- Explain how the parser/evidence extraction area should be refactored.

Files inspected:
- `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.1.run_basic_eval_v3.sh`
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/evaluation/opencode_skill_session.py`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/tests/test_mobius_monitor.py`
- `experiments/AgentCallInterface/tests/test_opencode_skill_session.py`

Result:
- No experiment code was changed.
- Identified OpenCode-specific responsibilities: clean restore/preparation, OpenCode skill artifact/runtime visibility capture, restarted-session skill invocation, and session reload classification.
- Identified Kilo-specific responsibilities: isolated workspace preparation, pre/post/cleanup state capture, timeout/subprocess cleanup, workspace/tmp cleanup verification, and summary note generation.
- Recommended moving generic evidence parsing from shell `grep` logic into Python, using `mobius_monitor.py` as the shared parser while keeping agent-specific environment operations in shell or dedicated Python helpers.

Follow-up request:
- Compare Claude Code, OpenCode, and Kilo Code execution flows.
- Determine whether shell-level initialization, workspace cleanup, and post-processing can be unified.
- Confirm that the first implementation step should be replacing shell `grep` parsing with `mobius_monitor.py`, leaving deeper flow unification for a second phase.

Follow-up result:
- Claude Code already encapsulates most execution differences in `ClaudeCodeCaller`: isolated per-task HOME/workspace under `/tmp/claude-code-runs/<run_id>`, OpenRouter env injection, and stream-json parsing.
- OpenCode uses a shared `/opencode` project directory and needs explicit cleanup plus restarted-session validation for newly created skills.
- Kilo Code uses a shared `/kilo_eval_workspace` and needs explicit workspace/tmp cleanup plus subprocess cleanup.
- The three agents can share the same high-level shell phases: backup, optional reset/prepare, pre-state capture, run injection, post-state capture, checkpoint, follow-up, cleanup verification, and Python evidence report.
- The safest first refactor remains replacing the shell `grep` evidence parsing with `mobius_monitor.py` while preserving current OpenCode reload and Kilo cleanup hooks.

Implementation:
- Updated `experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh` to call `experiments.AgentCallInterface.evaluation.mobius_monitor` after follow-up execution.
- Replaced the shell `grep`/`count_matches` generic evidence parser with `mobius_monitor.py` output.
- Changed the coding-agent summary columns to the existing Mobius monitor summary shape: Run Status, Skill Output, Skills Visible, Config State, Function Calls, Recursive Loops, Persistence, Notes.
- Preserved OpenCode restarted-session validation and Kilo cleanup checks as agent-specific notes outside the generic parser.
- Added `experiments/AgentCallInterface/tests/test_coding_eval_script.py` to guard the shell script against reintroducing generic output grep parsing.
- Added `experiments/AgentCallInterface/tests/test_coding_eval_monitor_e2e.py` to execute the `mobius_monitor.py` CLI against recorded output/follow-up/state fixtures and verify generated `analysis.json`, merged metrics, and summary fields.

Verification:
- `bash -n experiments/scripts/1.0.1.run_coding_agent_eval_v3.sh`: passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_mobius_monitor.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: failed before running tests because `pyarrow==24.0.0` has only cp310 wheels while the current interpreter is CPython 3.12.
- `PYTHONPATH=. python3 -m pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_mobius_monitor.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: 15 passed.
- `PYTHONPATH=. python3 -m pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_coding_eval_monitor_e2e.py experiments/AgentCallInterface/tests/test_mobius_monitor.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py`: 16 passed.
