# Session Record: Qwen36plus SWE-bench Claude Code Reparse Check

Date: 2026-04-28

## User Request

Dr. Frost asked whether SWE-bench has a newer Claude Code injection reparse result comparable to the HumanEval limit-20 reparse update.

## Check Performed

Scanned qwen36plus SWE-bench artifacts under `/home/zi/AgentCodingDos_CodeAgent/experiments/logs` for:

- `agent_summary.csv`
- `benchmark_summary.json`
- `manifest.json`

Also checked the existing result tables:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_swebench_agent_summary.csv`
- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_baseline_no_injection_limit20_swebench_agent_summary.csv`

## Result

No newer SWE-bench Claude Code injection reparse result was found.

The available SWE-bench qwen36plus summaries are:

- Original injection run: `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_swebench_agent_summary.csv`
- Baseline no-injection limit-20 result: `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_baseline_no_injection_limit20_swebench_agent_summary.csv`
- Claude raw baseline summary: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/swebench/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis/agent_summary.csv`

The HumanEval-only reparse directory exists at:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427`

but it contains no SWE-bench subdirectory or SWE-bench injection reparse summary.
