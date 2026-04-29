# Session Record: Direct Avg Call Summary

## User Request

Dr. Frost asked for a direct summary of average injected trace-record evidence calls for two benchmarks and three agents because the CSV is too noisy.

## Files

- `experiments/results/qwen36_v10_limit20_20260428/skill_call_agent_metrics.csv`

## Result

Primary average denominator: evidence-positive cases only.

| Benchmark | Agent | Avg trace-record evidence calls |
|---|---:|---:|
| HumanEval | claude_code | 12.73 |
| HumanEval | kilo_code | 12.55 |
| HumanEval | opencode | 12.20 |
| SWE-bench | claude_code | 7.33 |
| SWE-bench | kilo_code | 12.41 |
| SWE-bench | opencode | 12.53 |
