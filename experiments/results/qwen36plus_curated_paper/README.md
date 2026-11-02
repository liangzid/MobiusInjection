# Qwen 3.6 Plus Curated Paper Results

This folder contains the curated result set intended for paper metrics.

## Included Runs

Baseline, no injection, limit 20:

- HumanEval opencode/kilo_code: `experiments/logs/qwen36plus_baseline_no_injection_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus`
- HumanEval claude_code: `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus`
- SWE-bench opencode/kilo_code: `experiments/logs/qwen36plus_baseline_no_injection_20260427/swebench/models/openrouter_qwen_qwen3.6-plus`
- SWE-bench claude_code: `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/swebench/models/openrouter_qwen_qwen3.6-plus`

Injection:

- HumanEval opencode/kilo_code, limit 50: `experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus`
- HumanEval claude_code, limit 20: `experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus`
- SWE-bench opencode/kilo_code, limit 50:
  - first 20 from `experiments/logs/qwen36plus_sequential_20260424_183454/swebench/models/openrouter_qwen_qwen3.6-plus/manifest.json`
  - supplementary 30 from `experiments/logs/qwen36plus_sequential_20260424_183454/swebench/models/openrouter_qwen_qwen3.6-plus/manifest_supplement_20260426.json`
- SWE-bench claude_code, limit 20:
  - 18 from `experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/models/openrouter_qwen_qwen3.6-plus`
  - patched `DataDog__integrations-core-2041` and `DataDog__integrations-core-2282` from `experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_patch_20260428/swebench/models/openrouter_qwen_qwen3.6-plus`

## Files

- `paper_metrics.json`: full structured result.
- `paper_case_metrics.csv`: one row per selected case.
- `paper_agent_metrics.csv`: grouped by run kind, benchmark, and agent.
- `paper_metrics_report.md`: compact human-readable report.
- `source_selection.json`: exact source selection and filters.

## Current Summary

- Total cases: 360
- Completed cases: 360
- Baseline cases: 120
- Injection cases: 240
- Task run success rate: 0.7138888888888889
- Skill injection rate: 0.6638888888888889
- Skill file creation rate: 0.7055555555555556
- Regular tool calls: 8204
- Skill call events: 581
- Loop suspected rate: 0.9583333333333334

