# Session Record: Qwen36plus Results Export and No-Injection Baseline

Date: 2026-04-27

## User Request

Dr. Frost requested:

- Export HumanEval and SWE-bench `agent_summary.csv`-style result tables from the qwen36plus experiment into `/home/zi/AgentCodingDos_CodeAgent/experiments/results`.
- Run a no-injection baseline for HumanEval and SWE-bench with `limit=20`, using only the benchmark/task prompt and the same metric table format.

## Exported Existing Qwen36plus Results

- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_humaneval_agent_summary.csv`
- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_swebench_agent_summary.csv`

The SWE-bench table accounts for the known incomplete Claude Code run under the original qwen36plus root: `claude_code` has 21/50 completed analysis files while `opencode` and `kilo_code` have 50/50.

## No-Injection Baseline Runs

Baseline prompt mode: benchmark/task prompt only, no Mobius injection prompt.

Baseline output roots:

- All-agent baseline: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_baseline_no_injection_20260427`
- Claude raw baseline: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427`

Final combined baseline summaries:

- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_baseline_no_injection_limit20_humaneval_agent_summary.csv`
- `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_baseline_no_injection_limit20_swebench_agent_summary.csv`

For final combined baseline tables, `opencode` and `kilo_code` rows are sourced from the all-agent baseline. `claude_code` rows are sourced from the Claude raw baseline because that run preserves Claude stream/native tool-call events.

## Baseline Completion

HumanEval baseline:

- `claude_code`: 20/20 completed
- `kilo_code`: 20/20 completed
- `opencode`: 20/20 completed

SWE-bench baseline:

- `claude_code`: 20/20 completed
- `kilo_code`: 20/20 completed
- `opencode`: 20/20 completed

## Notes

- SWE-bench no-injection baseline contains many `response.success=False` cases. These are benchmark main-call failures/timeouts around 300 seconds, not injection failures. The baseline is intentionally no-injection, so skill injection rates should be 0.
- No baseline runner or agent CLI processes were left running after completion.
