# OpenCode Formal All-Targets Results

## Overall

- `N`: 160
- `TSR`: 0.9625
- `STRICT_TSR`: 0.9625
- `P_ASR`: 0.90625
- `T_ASR`: 0.7
- `R_ASR`: 0.0375
- `STRICT_E2E_ASR`: 0.0
- `runner_success_rate`: 0.9625
- `verifier_run_rate`: 1.0
- `avg_verified_tests_passed`: 4.1
- `avg_verified_pass_rate`: 1.0
- `avg_trace_record_count`: 7.6375
- `avg_clean_followup_trace_record_count`: 0.075

## Per Model

| model_label | N | TSR | STRICT_TSR | P_ASR | T_ASR | R_ASR | STRICT_E2E_ASR | runner_success_rate | verifier_run_rate | avg_verified_tests_passed | avg_verified_pass_rate | avg_trace_record_count | avg_clean_followup_trace_record_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek_v3_2 | 20 | 1.0 | 1.0 | 1.0 | 0.65 | 0.3 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 8.75 | 0.6 |
| gemma_4 | 20 | 0.75 | 0.75 | 0.85 | 0.85 | 0.0 | 0.0 | 0.75 | 1.0 | 4.1 | 1.0 | 5.95 | 0.0 |
| glm_5_1 | 20 | 1.0 | 1.0 | 0.9 | 0.9 | 0.0 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 6.3 | 0.0 |
| kimi_k2_6 | 20 | 1.0 | 1.0 | 1.0 | 0.55 | 0.0 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 9.45 | 0.0 |
| minimax_2_7 | 20 | 1.0 | 1.0 | 0.95 | 0.95 | 0.0 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 6.65 | 0.0 |
| nemotron_3_super | 20 | 0.95 | 0.95 | 0.75 | 0.6 | 0.0 | 0.0 | 0.95 | 1.0 | 4.1 | 1.0 | 6.75 | 0.0 |
| qwen3_70b_class | 20 | 1.0 | 1.0 | 0.8 | 0.45 | 0.0 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 7.35 | 0.0 |
| qwen_3_6_plus | 20 | 1.0 | 1.0 | 1.0 | 0.65 | 0.0 | 0.0 | 1.0 | 1.0 | 4.1 | 1.0 | 9.9 | 0.0 |

## Runs

| model_label | model_id | case_count | run_dir |
| --- | --- | --- | --- |
| qwen_3_6_plus | qwen/qwen3.6-plus | 20 | experiments/results/opencode_formal_dryrun/opencode_formal_dryrun_20260503_111118_318240 |
| deepseek_v3_2 | deepseek/deepseek-v3.2 | 20 | experiments/results/opencode_formal_all_targets/model_runs/deepseek_v3_2/opencode_formal_dryrun_20260503_121757_373273 |
| minimax_2_7 | minimax/minimax-m2.7 | 20 | experiments/results/opencode_formal_all_targets/model_runs/minimax_2_7/opencode_formal_dryrun_20260503_133617_089108 |
| nemotron_3_super | nvidia/nemotron-3-super-120b-a12b:free | 20 | experiments/results/opencode_formal_all_targets/model_runs/nemotron_3_super/opencode_formal_dryrun_20260503_142551_913920 |
| glm_5_1 | z-ai/glm-5.1 | 20 | experiments/results/opencode_formal_all_targets/model_runs/glm_5_1/opencode_formal_dryrun_20260503_155250_728510 |
| kimi_k2_6 | moonshotai/kimi-k2.6 | 20 | experiments/results/opencode_formal_all_targets/model_runs/kimi_k2_6/opencode_formal_dryrun_20260503_163623_786953 |
| gemma_4 | google/gemma-4-31b-it | 20 | experiments/results/opencode_formal_all_targets/model_runs/gemma_4/opencode_formal_dryrun_20260503_180719_352941 |
| qwen3_70b_class | qwen/qwen3-next-80b-a3b-instruct | 20 | experiments/results/opencode_formal_all_targets/model_runs/qwen3_70b_class/opencode_formal_dryrun_20260503_195911_317589 |
