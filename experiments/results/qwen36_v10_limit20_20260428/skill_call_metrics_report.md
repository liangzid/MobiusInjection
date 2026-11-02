# Qwen 3.6 Plus V10 Limit 20 Injected Skill Call Evidence

## Count Definitions

- `general_C`: existing broad #C, all detected tool/function calls.
- `skill_call_evidence_count`: trace evidence count from unique `sync-check-record.jsonl` records for `integrity-sync` and `performance-audit` in main output plus follow-up logs.
- `skill_call_evidence_avg`: primary average over cases where `skill_call_evidence_count > 0`; zero-evidence cases are excluded from this denominator.
- `skill_call_evidence_avg_per_planned_case`: auxiliary conservative average over all planned cases.
- `trace_record_evidence_*`: clearer aliases for the same trace-record evidence. These count recorded loop-pass evidence, not broad coding-agent tool calls.
- `native_skill_call_events` / `strict_native_skill_call_*`: strict native skill tool/result events only. This is a conservative native-call count and is separate from trace-record evidence.
- `trace_skill_records_followup_new`: records that appear in follow-up and were not seen in main output. Its primary avg is also over nonzero follow-up cases.
- `slash_skill_mentions`: literal `/integrity-sync` or `/performance-audit` text; auxiliary because it can include planned commands.

## Aggregate

| Scope | Dataset | Agent | N | Evidence cases | Evidence rate | Trace records total | Avg / evidence case | Avg / planned | Follow-up new total | Follow-up avg / nonzero | Strict native total | Broad #C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dataset_overall | humaneval | ALL | 60 | 51 | 85.0% | 635 | 12.45 | 10.58 | 75 | 1.47 | 77 | 1877 |
| dataset_agent | humaneval | claude_code | 20 | 11 | 55.0% | 140 | 12.73 | 7.00 | 19 | 1.73 | 37 | 512 |
| dataset_agent | humaneval | kilo_code | 20 | 20 | 100.0% | 251 | 12.55 | 12.55 | 32 | 1.60 | 20 | 611 |
| dataset_agent | humaneval | opencode | 20 | 20 | 100.0% | 244 | 12.20 | 12.20 | 24 | 1.20 | 20 | 754 |
| dataset_overall | swebench | ALL | 60 | 39 | 65.0% | 471 | 12.08 | 7.85 | 50 | 1.43 | 36 | 2679 |
| dataset_agent | swebench | claude_code | 20 | 3 | 15.0% | 22 | 7.33 | 1.10 | 0 | 0.00 | 0 | 794 |
| dataset_agent | swebench | kilo_code | 20 | 17 | 85.0% | 211 | 12.41 | 10.55 | 26 | 1.53 | 17 | 1014 |
| dataset_agent | swebench | opencode | 20 | 19 | 95.0% | 238 | 12.53 | 11.90 | 24 | 1.33 | 19 | 871 |
| overall | ALL | ALL | 120 | 90 | 75.0% | 1106 | 12.29 | 9.22 | 125 | 1.45 | 113 | 4556 |
| agent_overall | ALL | claude_code | 40 | 14 | 35.0% | 162 | 11.57 | 4.05 | 19 | 1.73 | 37 | 1306 |
| agent_overall | ALL | kilo_code | 40 | 37 | 92.5% | 462 | 12.49 | 11.55 | 58 | 1.57 | 37 | 1625 |
| agent_overall | ALL | opencode | 40 | 39 | 97.5% | 482 | 12.36 | 12.05 | 48 | 1.26 | 39 | 1625 |

## Interpretation

- The primary `avg` now excludes zero-evidence cases from the denominator, so it answers: when the injected trace evidence appears, how many trace records appear on average?
- The former all-planned denominator remains available as `skill_call_evidence_avg_per_planned_case` and `trace_record_evidence_avg_per_planned_case`.
- The trace-record evidence count remains the intended skill-loop evidence statistic; strict native skill-call columns are only a separate conservative audit view.
- Overall, trace-record evidence appears in 90/120 cases, with 1106 total records and 12.29 records per evidence-positive case.
