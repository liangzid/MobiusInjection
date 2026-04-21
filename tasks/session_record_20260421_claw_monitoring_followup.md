# Session Record - 2026-04-21 - Claw Monitoring Follow-up

## User Instruction

Execute `tasks/research_plan_0421_doubleCheckAll_claw_agents.org`, then pause when asked about the unresolved value of OpenClaw function calling.

## Files Touched

- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/evaluation/__init__.py`
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/tests/fixtures/real_zeroclaw_mobius_excerpt.txt`
- `experiments/AgentCallInterface/tests/test_mobius_monitor.py`
- `experiments/scripts/1.0.1.run_basic_eval_v3.sh`
- `experiments/__init__.py`
- `experiments/AgentCallInterface/__init__.py`
- `pyproject.toml`
- `tasks/session_record_20260421_claw_monitoring_followup.md`

## Work Performed

1. Reviewed the research plan, existing session record, claw caller layer, shell evaluation harness, and tests.
2. Added `mobius_monitor.py` to extract structured Mobius evidence from full agent output, follow-up output, captured skill/config state, Docker logs, and process snapshots.
3. Updated `1.0.1.run_basic_eval_v3.sh` to:
   - preserve full agent stdout/stderr instead of truncating it;
   - store response return codes and output lengths in API metrics;
   - read injection text from a file in Python instead of interpolating a large prompt into a heredoc;
   - capture Docker inspect, process listings, and Docker logs for each phase;
   - generate per-agent `*_analysis.json` files and merge the structured indicators back into metrics.
4. Extended `AgentResponse` to preserve stderr and return code for all caller paths.
5. Added pytest coverage for the structured Mobius monitor using a recorded ZeroClaw experiment excerpt.
6. Added package marker files and pytest `pythonpath` config so imports work under `uv run pytest`.

## Verification Performed

- `bash -n experiments/scripts/1.0.1.run_basic_eval_v3.sh`: passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile experiments/AgentCallInterface/agents/agent_callers.py experiments/AgentCallInterface/evaluation/mobius_monitor.py`: passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest experiments/AgentCallInterface/tests/test_agent_callers.py experiments/AgentCallInterface/tests/test_mobius_monitor.py`: 12 passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m experiments.AgentCallInterface.evaluation.mobius_monitor --output experiments/AgentCallInterface/tests/fixtures/real_zeroclaw_mobius_excerpt.txt --analysis /tmp/mobius_monitor_fixture_analysis.json`: passed.

## Runtime Execution Status

- Verified with approved `docker ps` that `hermes`, `nanobot`, `zeroclaw`, and `openclaw` containers are running.
- Requested approval to run the full four-agent evaluation with Docker commits/checkpoints and live OpenRouter-backed calls.
- The user interrupted before the full evaluation ran, so no new full injection run result was produced in this pass.

## OpenClaw Status

- OpenClaw is not fully fixed.
- The existing caller/config improvements remove the earlier wrapper-level and auth/profile-level blockers.
- The remaining problem is still the OpenClaw runtime/function-calling path: prior evidence shows empty payloads, `replayInvalid: true`, `livenessState: "abandoned"`, and no trustworthy function-call behavior.
- OpenClaw should still be classified as `runtime-broken` for this experiment setup until the installed OpenClaw build is upgraded/downgraded, patched, or routed through a normalizing workaround.
