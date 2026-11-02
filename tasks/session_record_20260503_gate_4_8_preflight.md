# Session Record - Gate 4-8 OpenCode Add-Skill Preflight - 2026-05-03

## User Request

- Complete Gate 4 through Gate 8 before the formal cross-model OpenCode add-skill experiment.
- Keep the framework aligned with the final large-scale experiment shape.
- Produce a summary document for review before starting the formal experiment.
- Continue recording commands, files, actions, results, and internal conclusions.

## Files Changed

- `experiments/configs/cross_model_opencode_add_skill_mobius_models.toml`
  - Added current model label to OpenRouter model ID mapping.
  - Recorded provider, timeout, candidate name, and resolution note.
- `experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py`
  - Added Gate 4-8 preflight harness.
  - Supports model dry-run manifest, real OpenCode connectivity matrix, timeout cleanup probe, 2x2 smoke aggregation, and scheduling summary.
  - Uses OpenCode only.
  - Does not use mock responses.
- `experiments/AgentCallInterface/tests/test_opencode_add_skill_preflight.py`
  - Tests config parsing, unresolved-label validation, manifest shape, connectivity classification, and smoke aggregation.
- `tasks/cross_model_opencode_add_skill_checklist_20260502.md`
  - Marked Gate 4-8 complete and added canonical results.
- `tasks/report_20260503_gate_4_8_preflight_summary.md`
  - User-facing summary report.
- `experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/`
  - First real run.
  - Useful negative/intermediate run:
    - Gemma free route timed out.
    - Qwen3 80B free route was model-unavailable.
    - Timeout cleanup process check had a pgrep self-match false negative.
- `experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003921_145594/`
  - Canonical passing Gate 4-8 run.

## Model ID Resolution

The current OpenRouter model catalog was queried on 2026-05-03.

Final model config:

| Label | Model ID | Result |
|---|---|---|
| `deepseek_v3_2` | `deepseek/deepseek-v3.2` | connectivity ok |
| `minimax_2_7` | `minimax/minimax-m2.7` | connectivity ok |
| `nemotron_3_super` | `nvidia/nemotron-3-super-120b-a12b:free` | connectivity ok |
| `glm_5_1` | `z-ai/glm-5.1` | connectivity ok |
| `kimi_k2_6` | `moonshotai/kimi-k2.6` | connectivity ok |
| `qwen_3_6_plus` | `qwen/qwen3.6-plus` | connectivity ok |
| `gemma_4` | `google/gemma-4-31b-it` | connectivity ok |
| `qwen3_70b_class` | `qwen/qwen3-next-80b-a3b-instruct` | connectivity ok |

Notes:

- The first Gemma 4 attempt used `google/gemma-4-31b-it:free` and timed out at 90s.
- The final Gemma 4 config uses paid `google/gemma-4-31b-it`, which completed in 36.078s.
- No current OpenRouter Qwen3 70B/72B text model was listed.
- The final Qwen 3 70B-class config uses the closest current Qwen3 80B-class instruct route.

## Canonical Run

Run directory:

- `experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003921_145594`

Generated files include:

- `run_manifest.json`
- `model_config_snapshot.json`
- `run_config_snapshot.json`
- `connectivity/connectivity_matrix.json`
- `connectivity/connectivity_matrix.csv`
- `connectivity/model_connectivity_report.md`
- `timeout_cleanup/timeout_cleanup_report.json`
- `aggregation_smoke/README.md`
- `aggregation_smoke/metrics_report.md`
- `aggregation_smoke/metrics.json`
- `aggregation_smoke/agent_metrics.csv`
- `aggregation_smoke/model_metrics.csv`
- `aggregation_smoke/case_metrics.csv`
- `aggregation_smoke/task_metrics.csv`
- `aggregation_smoke/trace_metrics.json`
- `aggregation_smoke/trace_case_metrics.csv`
- `scheduling_summary.json`
- `gate_4_8_report.md`

## Gate Results

### Gate 4 - External Model Configuration Dry Run

Result: passed.

- `run_manifest.json` generated 8 planned cases.
- Every case has model label, exact model ID, dataset, task ID, agent, timeout, run directory, and prompt hash.
- All cases use `agent=opencode`.
- No enabled model label was unresolved.

### Gate 5 - Model Connectivity Matrix

Result: passed.

All 8 enabled model routes returned real non-empty OpenCode responses.

Latency summary:

- Min: 2.851s.
- Max: 36.078s.
- Average: 8.489s.

No auth failure, model-unavailable failure, rate limit, provider error, or network error appeared in the canonical run.

### Gate 6 - Timeout And Cleanup

Result: passed.

- Forced timeout case timed out as expected.
- No `opencode run --dir /opencode` process remained after cleanup.
- Reset before and after the timeout returned status 0.
- Docker image count stayed unchanged: 75 before and 75 after.
- No Docker commit was used.

### Gate 7 - Result Aggregation Smoke Test

Result: passed.

- Smoke shape: 2 models x 2 HumanEval tasks.
- Real OpenCode calls were used.
- `TSR`: 1.0.
- Timeout rate: 0.0.
- Runtime failure rate: 0.0.
- The smoke package includes per-agent, per-model, per-task, per-case, and trace CSV/JSON outputs.

### Gate 8 - Cost, Rate Limit, And Scheduling

Result: passed.

- All candidate routes completed connectivity.
- No rate-limit behavior was observed.
- Recommended first formal run policy:
  - model-serial;
  - task-serial;
  - 300s per case;
  - preserve full raw logs.

## Verification

- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_add_skill_preflight.py`: 7 passed.
- `uv run --no-sync python -m py_compile experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py`: passed.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_add_skill_preflight.py experiments/AgentCallInterface/tests/test_opencode_realistic_skill_injection_probe.py experiments/AgentCallInterface/tests/test_opencode_two_skill_recursion_probe.py experiments/AgentCallInterface/tests/test_opencode_skill_session.py experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py`: 37 passed.
- `uv run --no-sync python -m py_compile experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py experiments/AgentCallInterface/coding_evaluation/opencode_realistic_skill_injection_probe.py experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py mobiusInjection/CODING_AGENT_TEMPLATE_OPENCODE_V10_REALISTIC.py`: passed.
- Secret scan over Gate 4-8 changed files and preflight result directories found no API key or Authorization hits.
- `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`: passed; `opencode debug skill` returned `[]`.

## Internal Conclusions

- The experiment framework for Gate 4-8 is ready for formal run preparation.
- Gate 3's autonomous skill-trigger effect remains a payload/effectiveness issue, not a framework blocker.
- For the first formal experiment, do not run model/task cases concurrently.
- Keep failed connectivity cases as infrastructure failures if any appear in future reruns.
