# Session Record: DeepSeek V4 Pro Formal Add-On

Date: 2026-05-05 15:05:27 HKT

## User Request

Add one more experiment group for the latest DeepSeek V4 model to the existing OpenCode all-target formal experiment results.

## Model Selection

I used `deepseek/deepseek-v4-pro` with model label `deepseek_v4_pro`.

Reason:

- OpenRouter lists `deepseek/deepseek-v4-pro` as DeepSeek V4 Pro, released 2026-04-24, with 1,048,576 context.
- V4 Pro is the flagship V4 variant for advanced reasoning, coding, and long-horizon agent workflows, while V4 Flash is the faster/economical variant.

Source checked:

- `https://openrouter.ai/deepseek/deepseek-v4-pro`

## Run Parameters

- `agent`: OpenCode
- `model_label`: `deepseek_v4_pro`
- `model`: `deepseek/deepseek-v4-pro`
- `limit`: 20
- `pass_threshold`: 2
- `timeout`: 420
- `verifier_timeout`: 60
- `output_root`: `experiments/results/opencode_formal_all_targets/model_runs/deepseek_v4_pro`

Command:

```bash
uv run --no-sync python -m experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun --model-label deepseek_v4_pro --model deepseek/deepseek-v4-pro --limit 20 --pass-threshold 2 --timeout 420 --verifier-timeout 60 --output-root experiments/results/opencode_formal_all_targets/model_runs/deepseek_v4_pro
```

## New Run Output

Run directory:

- `experiments/results/opencode_formal_all_targets/model_runs/deepseek_v4_pro/opencode_formal_dryrun_20260505_140342_225978`

DeepSeek V4 Pro original-metric summary:

| metric | value |
| --- | --- |
| N | 20 |
| TSR | 1.0 |
| STRICT_TSR | 1.0 |
| P_ASR | 1.0 |
| T_ASR | 0.75 |
| R_ASR | 0.05 |
| STRICT_E2E_ASR | 0.0 |
| runner_success_rate | 1.0 |
| verifier_run_rate | 1.0 |
| avg_verified_tests_passed | 4.1 |
| avg_verified_pass_rate | 1.0 |
| avg_trace_record_count | 6.55 |
| avg_clean_followup_trace_record_count | 0.1 |

## Updated Aggregate

New 9-model aggregate directory:

- `experiments/results/opencode_formal_all_targets/opencode_formal_all_targets_20260505_150335_532687`

Aggregate original-metric summary:

| metric | value |
| --- | --- |
| N | 180 |
| TSR | 0.9666666666666667 |
| STRICT_TSR | 0.9666666666666667 |
| P_ASR | 0.9166666666666666 |
| T_ASR | 0.7055555555555556 |
| R_ASR | 0.03888888888888889 |
| STRICT_E2E_ASR | 0.0 |
| runner_success_rate | 0.9666666666666667 |
| verifier_run_rate | 1.0 |
| avg_verified_tests_passed | 4.1 |
| avg_verified_pass_rate | 1.0 |
| avg_trace_record_count | 7.516666666666667 |
| avg_clean_followup_trace_record_count | 0.07777777777777778 |

## Updated Derived Main Trigger/Loop Metrics

Derived output files:

- `experiments/results/opencode_formal_all_targets/opencode_formal_all_targets_20260505_150335_532687/derived_main_trigger_loop_metrics.md`
- `experiments/results/opencode_formal_all_targets/opencode_formal_all_targets_20260505_150335_532687/derived_main_trigger_loop_metrics.csv`
- `experiments/results/opencode_formal_all_targets/opencode_formal_all_targets_20260505_150335_532687/derived_main_trigger_loop_case_metrics.csv`

DeepSeek V4 Pro derived row:

| model_label | N | TSR | STRICT_TSR | P_ASR | T_ASR_main_triggered | R_ASR_main_loop_after_trigger | STRICT_E2E_main_loop | avg_main_trace_record_count | avg_main_trace_rounds | original_T_ASR | original_R_ASR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek_v4_pro | 20 | 1.0 | 1.0 | 1.0 | 0.95 | 0.8 | 0.8 | 6.45 | 2.4 | 0.75 | 0.05 |

Updated overall derived row:

| model_label | N | TSR | STRICT_TSR | P_ASR | T_ASR_main_triggered | R_ASR_main_loop_after_trigger | STRICT_E2E_main_loop | avg_main_trace_record_count | avg_main_trace_rounds | original_T_ASR | original_R_ASR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OVERALL | 180 | 0.9666666666666667 | 0.9666666666666667 | 0.9166666666666666 | 0.9055555555555556 | 0.7333333333333333 | 0.7055555555555556 | 7.438888888888889 | 2.2 | 0.7055555555555556 | 0.03888888888888889 |

## Verification

Commands run:

```bash
uv run --no-sync pytest experiments/AgentCallInterface/tests/test_opencode_formal_results_aggregate.py experiments/AgentCallInterface/tests/test_opencode_formal_dryrun.py
uv run --no-sync python -m py_compile experiments/AgentCallInterface/coding_evaluation/opencode_formal_results_aggregate.py experiments/AgentCallInterface/coding_evaluation/opencode_formal_dryrun.py
targeted sensitive token scan over the DeepSeek V4 Pro run and the new 9-model aggregate directory
```

Results:

- Pytest: 14 passed.
- Py compile: passed.
- Sensitive token scan over the new DeepSeek V4 Pro run and new 9-model aggregate directory: no hits.
- New aggregate case rows: 180.
- New derived case rows: 180.
