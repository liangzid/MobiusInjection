# Session Record: Qwen36plus Final Artifact Check

Date: 2026-04-26

## User Request

Dr. Frost asked whether the qwen36plus HumanEval and SWE-bench experiments under `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454` had finished, whether the artifacts contained the expected 50-limit runs, whether sampled outputs ended normally, and where the final artifacts are located.

## Actions Taken

- Read manifest and artifact files under the specified experiment root.
- Counted unique tasks per benchmark and agent, including SWE-bench supplemental artifacts in `isolated_claude_supplement_20260426`.
- Sampled completed followup outputs for HumanEval and SWE-bench across `opencode`, `kilo_code`, and `claude_code`.
- Computed rates and tool-call metrics from existing `*_analysis.json` and `*_metrics.json` files.
- No experiment files were deleted, compressed, moved, or rerun.

## Findings

HumanEval is complete for the 50-limit setup:

- `opencode`: 50 / 50 analysis files
- `kilo_code`: 50 / 50 analysis files
- `claude_code`: 50 / 50 analysis files

SWE-bench is not fully complete:

- `opencode`: 50 / 50 analysis files
- `kilo_code`: 50 / 50 analysis files
- `claude_code`: 21 / 50 analysis files

The missing SWE-bench Claude Code tasks are:

- `DataDog__integrations-core-10093`
- `DataDog__integrations-core-1013`
- `DataDog__integrations-core-1019`
- `DataDog__integrations-core-10414`
- `DataDog__integrations-core-11210`
- `DataDog__integrations-core-1145`
- `DataDog__integrations-core-12675`
- `DataDog__integrations-core-1369`
- `DataDog__integrations-core-1403`
- `DataDog__integrations-core-14459`
- `DataDog__integrations-core-14649`
- `DataDog__integrations-core-1559`
- `DataDog__integrations-core-1570`
- `DataDog__integrations-core-1583`
- `DataDog__integrations-core-1620`
- `DataDog__integrations-core-1633`
- `DataDog__integrations-core-1731`
- `DataDog__integrations-core-1959`
- `DataDog__integrations-core-2041`
- `DataDog__integrations-core-2282`
- `django__django-11742`
- `django__django-11797`
- `django__django-11815`
- `django__django-11848`
- `django__django-11905`
- `django__django-11910`
- `django__django-11964`
- `django__django-11999`
- `django__django-12113`

## Metric Snapshot

HumanEval:

- `claude_code`: 50/50 complete, 50 success, skill injection 1.0, skills visible 1.0, persistence 1.0, recursive 1.0, total function calls 687, average 13.74, calls/min 2.85.
- `kilo_code`: 50/50 complete, 49 success and 1 failed, skill injection 1.0, skills visible 1.0, persistence 0.82, recursive 1.0, total function calls 5711, average 114.22, calls/min 23.29.
- `opencode`: 50/50 complete, 50 success, skill injection 1.0, skills visible 1.0, persistence 1.0, recursive 1.0, total function calls 5376, average 107.52, calls/min 29.29.

SWE-bench:

- `claude_code`: 21/50 complete, 9 success and 12 failed, skill injection 0.238, skills visible 0.667, persistence 0.476, recursive 0.667, total function calls 215, average 10.24, calls/min 5.10.
- `kilo_code`: 50/50 complete, 26 success and 24 failed, skill injection 0.9, skills visible 0.9, persistence 0.62, recursive 1.0, total function calls 5505, average 110.10, calls/min 13.17.
- `opencode`: 50/50 complete, 25 success and 25 failed, skill injection 1.0, skills visible 1.0, persistence 1.0, recursive 1.0, total function calls 4764, average 95.28, calls/min 17.31.

## Artifact Locations

- HumanEval model directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus`
- HumanEval logs: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/logs`
- HumanEval analysis directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis`
- SWE-bench model directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/swebench/models/openrouter_qwen_qwen3.6-plus`
- SWE-bench main logs: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/swebench/models/openrouter_qwen_qwen3.6-plus/logs`
- SWE-bench Claude supplement logs: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/swebench/models/openrouter_qwen_qwen3.6-plus/isolated_claude_supplement_20260426/logs`
