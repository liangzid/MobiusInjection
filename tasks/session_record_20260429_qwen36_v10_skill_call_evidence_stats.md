# Session Record: Qwen 3.6 Plus V10 Skill Call Evidence Stats

## User Request

Dr. Frost asked for an additional count of calls/evidence related only to the injected skills, noting that the evidence may not always appear as strict native skill calls and may require log analysis.

## Source Data

- HumanEval raw logs: `experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_limit20_20260428/models/openrouter_qwen_qwen3.6-plus/logs`
- SWE-bench raw logs: `experiments/logs/swebench_model_benchmark/qwen36_v10_swebench_limit20_20260428/models/openrouter_qwen_qwen3.6-plus/logs`
- Existing case metrics: `experiments/results/qwen36_v10_limit20_20260428/case_metrics.csv`

## New Output Files

- `experiments/results/qwen36_v10_limit20_20260428/skill_call_case_metrics.csv`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_agent_metrics.csv`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics.json`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics_report.md`

## Counting Logic

The previous `#C` was `counters.function_calls`, which includes all detected tool/function calls. The new primary count is `skill_call_evidence_count`:

- Count unique `sync-check-record.jsonl` records for `integrity-sync` and `performance-audit`.
- Use main output and follow-up logs only for the primary count.
- Deduplicate by `(run_id, skill, event, seq, argument_summary)`.
- Keep native skill tool/result events as a stricter auxiliary count.
- Keep literal `/integrity-sync` and `/performance-audit` mentions as auxiliary only because these can include planned commands.
- Keep a state-inclusive trace count in CSV/JSON for audit, but do not use it as the primary number because state snapshots can include transcript text.

## Key Results

Overall across 120 cases:

- Broad #C: 4556
- Injected skill evidence count: 1106
- Cases with injected skill evidence: 90/120
- Native skill events: 113
- Follow-up new trace records: 125

By benchmark:

- HumanEval: 635 skill evidence records across 51/60 cases.
- SWE-bench: 471 skill evidence records across 39/60 cases.

By agent across both benchmarks:

- `opencode`: 482 skill evidence records across 39/40 cases.
- `kilo_code`: 462 skill evidence records across 37/40 cases.
- `claude_code`: 162 skill evidence records across 14/40 cases.

## Interpretation

- The previous #C should be interpreted as broad tool/function activity, not injected skill calls.
- The new primary count better captures injected skill loop activity across agents.
- Native skill events are much lower because some agents execute the injected workflow through shell/file operations rather than a native skill engine.
