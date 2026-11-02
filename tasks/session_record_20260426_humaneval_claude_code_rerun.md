# Session Record: HumanEval Claude Code Rerun

Date: 2026-04-26

## User Request

Dr. Frost reported that after cleanup the HumanEval Claude Code experiment did not finish. The requested action was to remove the existing partial Claude Code outputs, rerun only the Claude Code HumanEval experiment, keep artifacts in the same experiment path for downstream processing, and periodically spot check for environment-related errors.

## Scope

- Experiment root: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454`
- HumanEval model path: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus`
- Target agent: `claude_code`
- Target benchmark entries: 50 HumanEval manifest entries for Claude Code

## Actions Taken

- Inspected the existing HumanEval Claude Code outputs and confirmed the previous partial run had only 11 completed analysis files, with one additional partial task output.
- Removed stale Claude Code files under the existing HumanEval `logs/` directory for all Claude Code manifest benchmark IDs. Other agents' outputs were left untouched.
- Stopped the previously running SWE-bench isolated Claude Code supplement process to avoid contention with the HumanEval rerun.
- Reran only the HumanEval Claude Code entries using the original HumanEval manifest and wrote outputs back into the same model `logs/` directory.
- Monitored the rerun with periodic environment checks for disk space, inode usage, `/tmp/claude-code-runs`, and output markers including:
  - `No space left on device`
  - `Container claude_code is paused`
  - `No such container`
  - `Rate limit`
  - `Authentication`
  - `anthropic_auth_token`
- Regenerated compact log retention metadata and the HumanEval benchmark analysis outputs in the same model directory.

## Results

- Claude Code HumanEval analysis files: 50 / 50
- Claude Code `run_status` count: `Success` = 50
- Environment marker hits in Claude Code output/followup files: 0
- Runner failures reported by rerun monitor: 0
- Environment failures reported by rerun monitor: 0
- Final observed disk state after the rerun:
  - Filesystem usage: 664G used / 170G available on an 879G overlay filesystem
  - Inode usage: 22%
  - `/tmp/claude-code-runs`: 4.0K, 0 files

## Artifacts

- Main output directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/logs`
- Rerun monitor log: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/worker_claude_code_rerun_20260426.log`
- Updated benchmark summaries: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/benchmark_summary.json`, `benchmark_summary.csv`, and `benchmark_report.md`
- Updated HumanEval metric analysis directory: `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_sequential_20260424_183454/humaneval/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis`

## Notes

- The rerun kept the same experiment path so downstream processing can continue using the existing HumanEval model directory.
- Experiment logs are ignored by git in this repository, so this record file captures the operational result in a tracked workspace location.
