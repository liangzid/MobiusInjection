# Gate 4-8 OpenCode Add-Skill Preflight Report

## Gate 4 - External Model Configuration Dry Run

- Planned cases: 8
- Agent: OpenCode only
- Invalid enabled model labels: none

## Gate 5 - Connectivity Matrix

| model_label | model_id | provider | status | success | duration_seconds | response_seconds | reset_status | response_file | resolution_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek_v3_2 | deepseek/deepseek-v3.2 | openrouter | ok | True | 3.94 | 3.94 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/deepseek_v3_2/response.json | Exact current OpenRouter ID. |
| minimax_2_7 | minimax/minimax-m2.7 | openrouter | ok | True | 5.623 | 5.623 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/minimax_2_7/response.json | Exact current OpenRouter ID. |
| nemotron_3_super | nvidia/nemotron-3-super-120b-a12b:free | openrouter | ok | True | 2.918 | 2.917 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/nemotron_3_super/response.json | Free current OpenRouter route for Nemotron 3 Super. |
| glm_5_1 | z-ai/glm-5.1 | openrouter | ok | True | 4.438 | 4.438 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/glm_5_1/response.json | Exact current OpenRouter ID. |
| kimi_k2_6 | moonshotai/kimi-k2.6 | openrouter | ok | True | 14.881 | 14.881 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/kimi_k2_6/response.json | Exact current OpenRouter ID. |
| qwen_3_6_plus | qwen/qwen3.6-plus | openrouter | ok | True | 7.581 | 7.58 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/qwen_3_6_plus/response.json | Exact current OpenRouter ID. |
| gemma_4 | google/gemma-4-31b-it:free | openrouter | timeout | False | 90.159 | 90.158 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/gemma_4/response.json | Free current Gemma 4 route; paid sibling is google/gemma-4-31b-it. |
| qwen3_70b_class | qwen/qwen3-next-80b-a3b-instruct:free | openrouter | model_unavailable | False | 1.341 | 1.341 | 0 | /home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/connectivity/qwen3_70b_class/response.json | No current OpenRouter Qwen3 70B/72B text model was listed; using the closest enabled Qwen3 80B-class instruct route for preflight. |

## Gate 6 - Timeout And Cleanup

- `model_label`: deepseek_v3_2
- `model_id`: deepseek/deepseek-v3.2
- `response_success`: False
- `timed_out`: True
- `reset_before_status`: 0
- `reset_after_status`: 0
- `opencode_processes_after_timeout`: 27721 bash -lc pgrep -af '/root/.opencode/bin/opencode run --dir /opencode' || true
- `opencode_process_cleanup_success`: False
- `docker_image_count_before`: 76
- `docker_image_count_after`: 76
- `docker_image_count_unchanged`: True
- `docker_commit_used`: False

## Gate 7 - Aggregation Smoke

- Smoke run directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/results/preflight_opencode_add_skill_mobius/gates_4_8_20260503_003518_458906/aggregation_smoke`
- `N`: 4
- `TSR`: 1.0
- `P_ASR`: 0.0
- `T_ASR`: 0.0
- `R_ASR`: 0.0
- `STRICT_E2E_ASR`: 0.0
- `trace_alternation_rate`: 0.0
- `trace_rounds_avg`: 0.0
- `timeout_rate`: 0.0
- `runtime_failure_rate`: 0.0

## Gate 8 - Cost, Rate Limit, And Scheduling

- `enabled_model_count`: 8
- `connectivity_success_count`: 6
- `connectivity_failures`: [{'model_label': 'gemma_4', 'status': 'timeout'}, {'model_label': 'qwen3_70b_class', 'status': 'model_unavailable'}]
- `latency_seconds_min`: 2.917
- `latency_seconds_max`: 14.881
- `latency_seconds_avg`: 6.563
- `timeout_cleanup_success`: False
- `recommended_policy`: Run model-serial and task-serial for the first full experiment; increase concurrency only after reset and cleanup remain stable.
- `recommended_case_timeout_seconds`: 300
