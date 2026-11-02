# Session Record: Qwen36plus SWE-bench Claude Code Injection Reparse Limit 20

Date: 2026-04-28

## User Request

Dr. Frost requested a new SWE-bench Claude Code injection experiment matching the prior HumanEval reparse setup, with `limit=20`, and then replacing the old Claude Code row in the SWE-bench injection results table.

## Experiment Configuration

- Benchmark: SWE-bench
- Dataset type: `verified_mini`
- Model: `openrouter/qwen/qwen3.6-plus`
- Agent: `claude_code`
- Limit: `20`
- Timeout per task: `300` seconds
- Prompt order: `task_before_injection`
- Log policy: `compact`

## Command Pattern

The run used:

```sh
MODEL_NAMES=openrouter/qwen/qwen3.6-plus CODING_EVAL_AGENTS=claude_code BENCHMARK_DATASET=swebench SWEBENCH_DATASET_TYPE=verified_mini LIMIT=20 TIMEOUT_SECONDS=300 FOLLOWUP_TIMEOUT_SECONDS=60 LOG_POLICY=compact BENCHMARK_RUN_DIR=/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench bash experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh
```

## Artifacts

- Run root: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench`
- Model root: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/models/openrouter_qwen_qwen3.6-plus`
- Metric summary: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis/agent_summary.csv`
- Updated result table: `/home/zi/AgentCodingDos_CodeAgent/experiments/results/qwen36plus_swebench_agent_summary.csv`

## Monitoring Notes

- The run completed all 20 planned cases.
- Structured analysis JSON was produced for all 20 cases.
- No infrastructure-level timeout or runtime failure was reported in the aggregate metrics.
- Several cases had runner failures, which were task-level unsuccessful agent runs within the experiment, not script/container failures.
- Cleanup succeeded after each checked case: run root, subprocesses, and tmp cleanup all reported clean.
- One case completed with runner success but no skill output/visibility; two later cases failed with no skill output/visibility and zero function calls. These were kept in the final statistics.

## Final Claude Code Row

The old SWE-bench injection `claude_code` row was replaced with:

```csv
claude_code,20,20,0,0.45,0.85,0.85,0.9,0.0,0.0,0.55,1446,72.3,83.5,550,896,20,202.2
```

The existing `kilo_code` and `opencode` rows were left unchanged.
