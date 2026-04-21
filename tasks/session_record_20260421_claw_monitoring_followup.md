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

## OpenClaw Config Repair Follow-up

### User Instruction

Dr. Frost asked to fix the OpenClaw configuration issue and use web search only if local evidence was insufficient.

### Files Touched

- `Env/setup/02_openclaw.sh`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/tests/test_openclaw_model_normalization.py`
- `tasks/session_record_20260421_claw_monitoring_followup.md`

### Container Files Changed

- `/root/.openclaw-mobius-eval/openclaw.json`
- `/root/.openclaw-mobius-eval/agents/main/agent/models.json`
- `/root/.openclaw-mobius-eval/agents/main/agent/models.json.bak-openrouter-baseurl-20260421`

### Work Performed

1. Inspected the active OpenClaw `mobius-eval` profile and verified that `openclaw --profile mobius-eval config validate --json` was schema-valid.
2. Verified OpenClaw auth/model status and confirmed the profile could see an OpenRouter API-key auth profile.
3. Reproduced the bad OpenClaw result with a minimal prompt:
   - `payloads=0`
   - zero usage
   - `Agent couldn't generate a response`
4. Tested the same OpenRouter key/model directly from inside the container:
   - `qwen/qwen3-coder:free` returned a direct OpenRouter `429` upstream rate-limit response.
   - `nvidia/nemotron-3-super-120b-a12b:free` returned a valid `OK` response directly from OpenRouter.
5. Added `openrouter/nvidia/nemotron-3-super-120b-a12b:free` to the OpenClaw `mobius-eval` allowed/default model config using `openclaw --profile mobius-eval models set`.
6. Isolated the remaining empty-turn symptom to the per-agent model catalog:
   - `/root/.openclaw-mobius-eval/agents/main/agent/models.json` had `providers.openrouter.baseUrl = "https://openrouter.ai/v1"`.
   - Running the installed pi-ai OpenAI-completions parser against that URL reproduced the exact empty-content, zero-usage, `stop` result.
7. Patched the per-agent model catalog to use:
   - `https://openrouter.ai/api/v1`
8. Verified that OpenClaw now returns a valid result:
   - CLI path: `openclaw --profile mobius-eval infer model run --local --json --model openrouter/nvidia/nemotron-3-super-120b-a12b:free --prompt "Reply with exactly OK"` returned `OK`.
   - Python caller path with model `nvidia/nemotron-3-super-120b-a12b:free` returned `{'success': True, 'output': 'OK', 'error': None, 'returncode': 0}`.
9. Updated `OpenClawCaller` to normalize OpenRouter model ids by adding the `openrouter/` provider prefix when the evaluation passes raw OpenRouter model ids such as `nvidia/nemotron-3-super-120b-a12b:free`.
10. Updated `Env/setup/02_openclaw.sh` so future OpenClaw setup creates a valid `mobius-eval` profile, auth store, corrected OpenRouter base URL, and default allowed model.

### Verification Performed

- `bash -n Env/setup/02_openclaw.sh`: passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest experiments/AgentCallInterface/tests/test_openclaw_model_normalization.py experiments/AgentCallInterface/tests/test_mobius_monitor.py`: 6 passed.
- `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile experiments/AgentCallInterface/agents/agent_callers.py`: passed.
- Live OpenClaw CLI smoke test: passed with output `OK`.
- Live project Python caller smoke test: passed with `success=True` and output `OK`.
- Docker backup image created:
  - `openclaw:mobius_eval_config_fixed_20260421`
  - image id `sha256:3b8f723fe729ee09694e762a1140d0764f0fb0be741952cdad578b7b14e69019`

### Updated OpenClaw Conclusion

- The concrete OpenClaw configuration issue is fixed.
- The prior empty-turn symptom was caused by the stale per-agent OpenRouter base URL `https://openrouter.ai/v1`, not by OpenRouter auth.
- OpenClaw is now usable for simple model turns through the current Python caller path.
- A full Mobius injection run was not executed in this follow-up, so recursive/function-call behavior still needs a dedicated evaluation pass.
