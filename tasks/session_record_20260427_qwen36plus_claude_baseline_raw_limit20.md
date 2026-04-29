# Session Record: Qwen3.6 Plus Claude Code Baseline Limit 20

Date: 2026-04-27

## User Request

Run the newly fixed Claude Code recording/parser path on baseline experiments for:

- HumanEval
- SWE-bench
- Agent: `claude_code`
- Model: `openrouter/qwen/qwen3.6-plus`
- Prompt condition: benchmark description/tasks only, no project prompt/injection prompt
- Limit: 20 tasks per benchmark

The user asked to reuse prior scripts or prior run patterns where possible.

## Execution Notes

- Found a prior baseline artifact directory: `experiments/logs/qwen36plus_baseline_no_injection_20260427`.
- A stale older baseline process from that run was still active and interfering with the `claude_code` container.
- Killed the stale runner and child Claude processes before starting the clean run.
- Started a fresh run in:
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427`
- The run used benchmark-only prompts and wrote raw Claude stream output plus parsed output and metrics.

## Artifacts

- Top-level summary:
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/baseline_summary.json`
- HumanEval summary:
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus/baseline_run_summary.json`
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/humaneval/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis/agent_summary.csv`
- SWE-bench summary:
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/swebench/models/openrouter_qwen_qwen3.6-plus/baseline_run_summary.json`
  - `experiments/logs/qwen36plus_claude_baseline_raw_limit20_20260427/swebench/models/openrouter_qwen_qwen3.6-plus/agent_metric_analysis/agent_summary.csv`

## Results

HumanEval, limit 20:

- Completed cases: 20/20
- Runner success rate: 18/20 = 0.90
- Total function calls: 32
- Average function calls: 1.60
- Median function calls: 1.0
- Total native tool calls: 32
- Total textual function calls: 0
- Raw output chars: 930,481 total, 46,524 average
- Average duration: 12.38 seconds
- Failures:
  - `HumanEval/0`: return code 143, raw output 12,650 chars, 1 native tool call
  - `HumanEval/4`: return code 143, raw output 4,478 chars, 0 native tool calls

SWE-bench, limit 20:

- Completed cases: 20/20
- Runner success rate: 6/20 = 0.30
- Total function calls: 741
- Average function calls: 37.05
- Median function calls: 34.5
- Total native tool calls: 741
- Total textual function calls: 0
- Raw output chars: 14,575,757 total, 728,788 average
- Average duration: 287.00 seconds
- Several failed cases ran to about 300 seconds and returned unsuccessful responses, but still produced large raw streams and nonzero native tool-call counts.

## Spot Checks

Raw stream spot checks were performed after the run:

- HumanEval `HumanEval/6`:
  - Raw file: `humaneval_HumanEval_6_claude_code_d8aeb3c2f64f_claude_code_output.txt`
  - JSON lines: 351
  - Unique `tool_use` ids: 6
  - Unique `tool_result` ids: 6
  - Matches summary native tool-call count: 6
- SWE-bench `DataDog__integrations-core-10093`:
  - Raw file: `swebench_DataDog__integrations-core-10093_claude_code_795139174dff_claude_code_output.txt`
  - JSON lines: 2,215
  - Unique `tool_use` ids: 32
  - Unique `tool_result` ids: 32
  - Matches summary native tool-call count: 32

The raw stream can contain duplicate appearances of the same tool use in different Claude stream envelopes. Counting unique tool-call ids is required to avoid over-counting; the updated parser does this.

## Conclusion

The clean benchmark-only Claude Code/Qwen3.6 Plus baseline output looks normal under the raw-stream recording path.

The previous unusually low function-call counts are consistent with a recording/parsing issue that failed to preserve or parse Claude Code's native JSON stream. With raw stream recording and native `tool_use` parsing, HumanEval remains low-call as expected for short tasks, while SWE-bench rises to tens of native tool calls per task.

## Follow-up: SWE-bench Failure Cause Check

The 14 unsuccessful SWE-bench cases were checked after the user asked what the failures meant.

Findings:

- All 14 unsuccessful SWE-bench cases had durations at about 300 seconds:
  - Minimum failure duration: about 300.01 seconds
  - Maximum failure duration: about 300.03 seconds
- All 14 had `returncode: null` in the recorded `AgentResponse`, which matches the Claude Code caller's `subprocess.TimeoutExpired` handling path.
- These failures are therefore operationally 300-second caller timeouts, not benchmark correctness failures and not ordinary nonzero process exits.
- The `timed_out` field in the analyzer summary was misleadingly `false` for these cases because `timed_out` is currently inferred by regex from output text. The Claude timeout path preserved partial parsed assistant text as `error`, so the saved output did not necessarily contain the literal `Timeout after 300s` string that the analyzer expects.
- Raw stream tails show the agent was still active when interrupted in many cases, often in thinking/tool-use phases such as reading files, cloning or inspecting repository history, finding historical commits, or preparing further tool calls.

Conclusion:

The SWE-bench failures in this run should be interpreted as 300-second budget expirations. The analyzer timeout field should be fixed or supplemented with structured caller metadata before using timeout rate as a reliable metric.
