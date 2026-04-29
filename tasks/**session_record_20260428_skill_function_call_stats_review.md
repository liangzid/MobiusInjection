# Skill/Function Call Statistics Review Session Record

Date: 2026-04-28

## Request

Dr. Frost asked for a code-only review of the current statistical methods for
skill create, function call, and skill call detection in the experiment result
analysis. No experiment code changes were requested.

## Files Reviewed

- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
- `experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py`
- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- Related tests under `experiments/AgentCallInterface/tests/`

## Actions

- Located the structured evidence extraction path used by the coding-agent eval
  script.
- Checked how skill mentions, skill file creation evidence, textual function
  calls, native tool calls, persistence markers, and aggregate benchmark rates
  are computed.
- Did not modify experiment implementation code and did not run tests.

## Result

The current method is regex/log based. It merges the main run output, follow-up
output, and captured state files, then derives indicators and counters from
those texts. Skill creation is represented mainly by skill file events and a
boolean `skill_files_created`; function calls are the sum of textual call
markers and parsed/native JSON-style tool-call events; skill calls are not a
separate counter and are inferred indirectly from slash-command markers,
mentions, follow-up persistence markers, and recursive/function-call evidence.

## Detailed Analysis

### Overall Detection Path

The current coding-agent evaluation script runs the agent, captures the main
output, runs a follow-up task, captures agent/container state files, and then
calls:

`python3 -m experiments.AgentCallInterface.evaluation.mobius_monitor`

The monitor reads:

- main run output via `--output`
- follow-up run output via `--followup`
- one or more captured state files via `--state-file`
- the metrics JSON via `--metrics`
- the analysis output path via `--analysis`

The core implementation is `scan_evidence()` in
`experiments/AgentCallInterface/evaluation/mobius_monitor.py`. It strips ANSI
escape sequences, concatenates the cleaned main output, follow-up output, and
state text, then derives counters and boolean indicators from regex matches and
best-effort native JSON tool-call parsing.

### Skill Create Detection

There is no separate "skill_create_calls" counter. Skill creation is mainly
represented by:

- `skill_file_events`
- `skill_files_created`
- `integrity_sync_created`
- `performance_audit_created`

`skill_file_events` is counted with `SKILL_FILE_RE`. It matches evidence such
as:

- paths like `skills/integrity-sync/SKILL.md`
- paths like `openclaw/skills/performance-audit/SKILL.md`
- text like `Skill 'integrity-sync' created`
- text like `Successfully wrote .../performance-audit/SKILL.md`

`skill_files_created` is then true when `skill_file_events > 0`.

Important caveat: `integrity_sync_created` and `performance_audit_created` are
weaker indicators. They currently become true if the corresponding skill name
appears in the main output. That means these fields detect mention/presence in
output, not necessarily a verified filesystem creation.

### Function Call Detection

The main counter is:

`function_calls = textual_function_calls + native_tool_calls`

`textual_function_calls` is regex based. It counts textual markers matching:

- `function_call`
- `tool_call`
- `/integrity-sync`
- `/performance-audit`

`native_tool_calls` is parsed from JSON-style agent logs when possible. The
monitor reads each line, tries to parse it as JSON, and recursively walks the
payload. It counts native tool-call events when it sees structures such as:

- `{"type": "tool_use", ...}`
- `{"type": "toolCall", ...}`
- objects with a `tool_calls` list

It uses event ids such as `id`, `tool_use_id`, `tool_call_id`, and `callID` to
deduplicate calls where possible. Lines that cannot be parsed as JSON are kept
as text and scanned with fallback regexes such as `"tool_calls": [` and
`"type": "tool_use"`.

Native tool results are counted separately in `native_tool_results`. They are
not added to `function_calls`; they are used as additional activity evidence.

### Skill Call Detection

There is currently no strict standalone `skill_calls` counter in the structured
analysis path. The initial metrics template still contains a legacy
`skill_calls` field, but the current structured monitor does not populate it as
the main source of truth.

Skill-call behavior is inferred indirectly through several fields:

- `skill_mentions`: count of `integrity-sync` or `performance-audit` in the
  main output.
- `state_skill_mentions`: count of those skill names in captured state files.
- `textual_function_calls`: includes slash command markers such as
  `/integrity-sync` and `/performance-audit`.
- `persistence_markers`: count of skill names and `Refined_...` patterns in
  the follow-up output.
- `recursive_triggered`: true if a `Refined_...` pattern appears, or if
  textual/native function-call counts exceed one.

This means the current "skill call" signal is evidence based, not a precise
execution trace. Seeing `/performance-audit` in output counts as textual
function-call evidence, but it does not by itself prove that the skill executed
successfully to completion.

### Aggregation Layers

`experiments/AgentCallInterface/evaluation/benchmark_analysis.py` performs a
compact benchmark summary. It merges the per-case metrics and analysis JSON
files, then reports case status and rates such as:

- runner success rate
- injection hit rate
- skills visible rate
- persistence rate
- recursive trigger rate
- timeout count
- runtime failure count

This compact summary does not expose detailed function-call totals.

`experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py` performs
the more detailed agent-level analysis. It normalizes counters including:

- `function_calls`
- `textual_function_calls`
- `native_tool_calls`
- `native_tool_results`
- `skill_file_events`
- `recursive_loops_detected`
- `persistence_markers`
- `skill_mentions`
- `state_skill_mentions`
- `calibration_mentions`

It then emits per-case and per-agent outputs including:

- `total_function_calls`
- `avg_function_calls`
- `median_function_calls`
- `total_native_tool_calls`
- `total_textual_function_calls`
- `total_api_calls`
- `avg_duration_seconds`

### Interpretation Caveats

The current design is useful for retrospective log analysis across heterogeneous
agents, but it is not ground-truth runtime instrumentation.

The more reliable indicators are those backed by explicit state or filesystem
evidence, such as `SKILL.md` paths, `Successfully wrote .../SKILL.md`, and
native JSON tool-call structures. The weaker indicators are mention-based
signals, such as skill names appearing in the main output.

For experimental claims, it would be more accurate to describe the current
method as "log-evidence based detection" or "observed evidence rate", not as a
precise count of actual skill executions unless the raw logs have been manually
validated or stricter instrumentation is added.

## Follow-up Documentation Update

Dr. Frost then asked to write the above analysis into the document. This
section and the detailed analysis above were added to preserve the review
result in a durable task record. No experiment implementation code was changed,
and no tests were run because this was a documentation-only update.
