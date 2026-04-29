# Session Record: Qwen36plus HumanEval Claude Code Reparse Result Update

Date: 2026-04-28

## User Request

Dr. Frost requested updating the HumanEval qwen36plus result table by removing the old Claude Code row with undercounted function calls and replacing it with the newer limit-20 injection reparse result. No new experiment run was requested.

## Files Touched

- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_humaneval_agent_summary.csv`
- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis/agent_summary.csv`

## Source Artifact

The replacement Claude Code row was generated from:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus`

The analysis output directory is:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis`

## Result

Replaced the old HumanEval `claude_code` summary row:

- Old: `planned_cases=50`, `completed_cases=50`, `total_function_calls=687`, `avg_function_calls=13.74`, `total_native_tool_calls=0`, `total_textual_function_calls=687`

With the reparse limit-20 row:

- New: `planned_cases=20`, `completed_cases=20`, `total_function_calls=1249`, `avg_function_calls=62.45`, `median_function_calls=56.0`, `total_native_tool_calls=281`, `total_textual_function_calls=968`

The `kilo_code` and `opencode` rows in the result table were left unchanged.
