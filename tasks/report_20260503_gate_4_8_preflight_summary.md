# Gate 4-8 Preflight Summary - OpenCode Add-Skill Mobius - 2026-05-03

## Executive Summary

Gate 4-8 are complete for framework readiness.

The canonical run is:

- `experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003921_145594`

All 8 configured model routes passed real OpenCode connectivity. Timeout cleanup passed. The 2 models x 2 HumanEval aggregation smoke test produced the required result package shape.

Gate 3's remaining issue is effect-side only: clean follow-up did not passively trigger project skills for the tested OpenCode/model pair. The Gate 4-8 framework can proceed; later payload work can tune skill metadata to improve trigger behavior.

## Final Model Matrix

| Label | OpenRouter model ID | Connectivity | Latency |
|---|---|---:|---:|
| `deepseek_v3_2` | `deepseek/deepseek-v3.2` | ok | 3.358s |
| `minimax_2_7` | `minimax/minimax-m2.7` | ok | 9.500s |
| `nemotron_3_super` | `nvidia/nemotron-3-super-120b-a12b:free` | ok | 3.048s |
| `glm_5_1` | `z-ai/glm-5.1` | ok | 4.352s |
| `kimi_k2_6` | `moonshotai/kimi-k2.6` | ok | 4.373s |
| `qwen_3_6_plus` | `qwen/qwen3.6-plus` | ok | 4.348s |
| `gemma_4` | `google/gemma-4-31b-it` | ok | 36.078s |
| `qwen3_70b_class` | `qwen/qwen3-next-80b-a3b-instruct` | ok | 2.851s |

Notes:

- `gemma_4` uses the paid route because `google/gemma-4-31b-it:free` timed out during the first preflight.
- OpenRouter did not list an exact Qwen3 70B/72B text model. The current config uses the closest Qwen3 80B-class instruct route.

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| Gate 4 external config dry-run | passed | `run_manifest.json` has 8 OpenCode-only cases; no unresolved enabled labels |
| Gate 5 connectivity matrix | passed | all 8 model routes returned real non-empty OpenCode responses |
| Gate 6 timeout cleanup | passed | forced timeout killed OpenCode run process; image count unchanged; no Docker commit |
| Gate 7 aggregation smoke | passed | 2x2 real OpenCode smoke package generated metrics JSON/CSV/Markdown |
| Gate 8 scheduling | passed | latency/rate-limit summary generated; no rate limits observed |

## Result Package Check

Aggregation smoke directory:

- `experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003921_145594/aggregation_smoke`

Generated files:

- `README.md`
- `metrics_report.md`
- `metrics.json`
- `agent_metrics.csv`
- `model_metrics.csv`
- `case_metrics.csv`
- `task_metrics.csv`
- `trace_metrics.json`
- `trace_case_metrics.csv`
- `run_manifest.json`
- `run_config_snapshot.json`
- `failure_examples.md`

Smoke metrics:

- `N`: 4
- `TSR`: 1.0
- `timeout_rate`: 0.0
- `runtime_failure_rate`: 0.0

The smoke run intentionally does not execute the add-skill payload, so `P_ASR`, `T_ASR`, `R_ASR`, and `STRICT_E2E_ASR` are all 0.0 in this package.

## Scheduling Recommendation

Use this for the first formal run:

- Run model-serial.
- Run task-serial.
- Keep timeout at 300s per case.
- Preserve full raw logs.
- Keep reset before every case and cleanup after timeout enabled.
- Do not raise concurrency until one full serial run confirms no cross-case contamination.

## Risks Before Formal Run

- Gate 3 autonomous clean follow-up did not trigger skills. This is an injection-effect issue, not a Gate 4-8 framework issue.
- The Qwen3 70B candidate is not an exact 70B route. The current route should be treated as `qwen3_70b_class`, not a strict 70B model.
- Gemma 4 is slower than the other connectivity cases and should keep the 300s timeout.

## Next Formal-Run Inputs

- Model config: `experiments/configs/cross_model_opencode_add_skill_mobius_models.toml`
- Gate 4-8 harness: `experiments/AgentCallInterface/coding_evaluation/opencode_add_skill_preflight.py`
- Current realistic OpenCode template: `mobiusInjection/CODING_AGENT_TEMPLATE_OPENCODE_V10_REALISTIC.py`
- Current trace monitor: `experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py`
- Reset script: `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`
