# Session Record: Claude Code Function-Call Recording Investigation

Date: 2026-04-27

## User Request

Dr. Frost observed that Claude Code appears to have much lower function-call counts under injection, and asked to investigate whether recording, pre-processing, or post-processing could be causing unusually low function-call statistics. The user explicitly asked not to run experiments and not to modify code.

## Scope

- Reviewed existing scripts and logs only.
- No experiments were run.
- No production or experiment code was modified.

## Files Inspected

- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`
- `experiments/AgentCallInterface/agents/agent_callers.py`
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py`
- `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
- `experiments/AgentCallInterface/evaluation/log_retention.py`
- Existing qwen3.6-plus HumanEval and baseline analysis artifacts under `experiments/logs/`
- Existing qwen3.6-plus summary CSVs under `experiments/results/`

## Findings

- Claude Code is invoked with `--output-format stream-json`, but `ClaudeCodeCaller._parse_claude_stream_response()` converts the raw event stream into assistant text only before returning `AgentResponse.output`.
- The benchmark script records only `response.output` into `*_claude_code_output.txt`, so Claude Code native tool events are discarded before `mobius_monitor` scans the file.
- OpenCode and Kilo Code callers preserve raw JSON output in `response.output`, so their saved output files include many `tool_use` events and repeated skill names.
- `mobius_monitor` counts `function_calls` via regex over saved output, followup, and state text. Its `FUNCTION_CALL_RE` includes `tool_use`, `/integrity-sync`, and `/performance-audit`, while `NATIVE_TOOL_CALL_RE` does not match OpenCode/Kilo `{"type":"tool_use"}` events.
- Existing qwen3.6-plus HumanEval summaries show `native_tool_calls=0` for all agents. Therefore current `function_calls` are text-derived counts, not a reliable cross-agent native function-call metric.
- In one sampled HumanEval case, Claude Code output contained no `tool_use`/`callID` records, while OpenCode and Kilo Code outputs contained raw JSON tool events. This explains why Claude Code can look much quieter even when it performed tool actions.
- Existing post-injection state files add additional skill-name occurrences. These are evidence of artifacts/visibility, but they are also mixed into the `function_calls` regex input, further making the count a textual-evidence metric rather than actual call count.

## Metric Snapshot From Existing Artifacts

HumanEval qwen3.6-plus injection:

- `claude_code`: 50 completed, total function calls 687, average 13.74, native 0, textual 687.
- `kilo_code`: 50 completed, total function calls 5711, average 114.22, native 0, textual 5711.
- `opencode`: 50 completed, total function calls 5376, average 107.52, native 0, textual 5376.

HumanEval qwen3.6-plus no-injection baseline:

- `claude_code`: 20 completed, total function calls 0, native 0, textual 0.
- `kilo_code`: 20 completed, total function calls 119, native 0, textual 119.
- `opencode`: 20 completed, total function calls 405, native 0, textual 405.

## Internal Result

There is a plausible and concrete recording/statistics artifact: Claude Code raw stream tool events are dropped during caller parsing, while OpenCode and Kilo Code raw JSON events are retained. The current cross-agent `function_calls` column should not be interpreted as comparable actual function/tool-call counts. It is better described as a textual evidence count from post-processed logs and state files.
