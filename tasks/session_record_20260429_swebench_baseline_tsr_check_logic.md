# Session Record: SWE-bench Baseline TSR Check Logic

## User Request

Dr. Frost asked why SWE-bench baseline TSR is low and whether the current check logic can be inspected.

## Files Inspected

- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py`
- `experiments/results/qwen36plus_baseline_no_injection_limit20_swebench_agent_summary.csv`
- `experiments/logs/qwen36plus_baseline_no_injection_20260427/swebench/models/openrouter_qwen_qwen3.6-plus/manifest.json`
- `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/swebench/models/openrouter_qwen_qwen3.6-plus/manifest.json`
- Sample SWE-bench output and metrics files under the two baseline run directories.

## Findings

- Current TSR is `runner_succeeded`.
- `runner_succeeded` is set by `SUCCESS_RE = re.compile(r"Success:\s*True")` in `mobius_monitor.py`.
- The `Success: True` text is printed by the wrapper from `AgentResponse.success`.
- Agent success is CLI-level:
  - OpenCode: command return code 0 and stderr does not look like provider/model error.
  - Kilo Code: command return code 0.
  - Claude Code: return code 0, final payload not error, and non-empty assistant text.
- The current SWE-bench path does not run the official SWE-bench patch evaluator or test harness. It does not directly validate that a generated patch solves the task.
- SWE-bench baseline tasks are harder than HumanEval because the prompt contains issue metadata and test patch, but the agent workspace can start empty. Agents often spend time discovering/cloning/exploring the repo.
- For OpenCode/Kilo baseline SWE-bench, most failures are timeout/runtime-failure cases.
- For Claude baseline SWE-bench, many failures are CLI/stream-level failures or empty/no usable completion, not official test failures.

## Baseline SWE-bench Summary

- `claude_code`: 30.0% TSR in the curated raw baseline.
- `kilo_code`: 30.0% TSR.
- `opencode`: 35.0% TSR.
- Overall: 31.7% TSR across 60 planned cases.

## Interpretation

The low SWE-bench baseline TSR mostly reflects harness/agent completion under a time budget, repo setup friction, and task complexity. It should not be interpreted as official SWE-bench resolved-rate. For official TSR, the harness would need to pre-checkout the target repo/version, capture patches, and run SWE-bench evaluation tests.
