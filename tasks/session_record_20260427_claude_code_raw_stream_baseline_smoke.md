# Session Record: Claude Code Raw Stream Baseline Smoke

Date: 2026-04-27

## User Request

Dr. Frost asked to modify the Claude Code caller so raw output stream events are available, run a few HumanEval baseline tasks without injection, check whether outputs look normal, parse the normal output stream, and report whether function-call counts rise before taking next steps.

## Code Changes

- `experiments/AgentCallInterface/agents/agent_callers.py`
  - Added `AgentResponse.raw_output`.
  - Preserved Claude Code raw stdout stream in `raw_output` while keeping parsed assistant text in `output`.
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
  - Added JSON-line native tool activity parsing.
  - Counted `tool_use` / `tool_result` events from Claude Code stream JSON.
  - Deduplicated tool events by tool-use id / call id.
  - Kept textual slash-skill evidence separate from native tool-call evidence.
- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
  - Saved `response.raw_output` when available for injection and follow-up outputs.
  - Recorded `recorded_output_chars` in API metrics.
- Tests updated:
  - `experiments/AgentCallInterface/tests/test_agent_callers.py`
  - `experiments/AgentCallInterface/tests/test_mobius_monitor.py`

## Verification

- `uv run --no-sync --with pytest --python /usr/bin/python3.10 pytest experiments/AgentCallInterface/tests/test_agent_callers.py experiments/AgentCallInterface/tests/test_mobius_monitor.py`
  - Result: 25 passed.
- `uv run --no-sync --with pytest --python /usr/bin/python3.10 pytest experiments/AgentCallInterface/tests/test_coding_eval_script.py experiments/AgentCallInterface/tests/test_coding_eval_monitor_e2e.py`
  - Result: 12 passed.

## Baseline Smoke Run

- Run directory: `experiments/logs/claude_raw_stream_baseline_smoke_20260427`
- Agent: `claude_code`
- Model: `openrouter/qwen/qwen3.6-plus`
- Injection: none
- HumanEval tasks: `HumanEval/0`, `HumanEval/1`, `HumanEval/2`
- `CLAUDE_CODE_MAX_TURNS=20`

Results after deduplicated raw-stream parsing:

- `HumanEval/0`: success true, raw output 93,650 chars, parsed output 796 chars, native tool calls 5, function calls 5.
- `HumanEval/1`: success true, raw output 94,946 chars, parsed output 403 chars, native tool calls 4, function calls 4.
- `HumanEval/2`: success true, raw output 28,974 chars, parsed output 79 chars, native tool calls 1, function calls 1.

Existing old qwen3.6-plus no-injection baseline metrics for the same three Claude Code tasks reported:

- `HumanEval/0`: function calls 0, native tool calls 0.
- `HumanEval/1`: function calls 0, native tool calls 0.
- `HumanEval/2`: function calls 0, native tool calls 0.

## Internal Result

The output stream is normal: Claude Code returned successful parsed text for all three baseline tasks, and raw stream artifacts contain structured `tool_use` events. After preserving and parsing the raw stream, Claude Code baseline function/tool-call counts rose from 0 to nonzero values on all three sampled tasks. This confirms the prior low Claude Code function-call count was at least partly a recording/parsing artifact.
