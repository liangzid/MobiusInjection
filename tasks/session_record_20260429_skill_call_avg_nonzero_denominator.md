# Session Record: Skill Call Average Nonzero Denominator

## User Request

Dr. Frost clarified that `avg` should be computed only over cases where trace-record evidence appears. Zero-evidence cases should not be included in the denominator. Dr. Frost also clarified that the trace-record evidence statistic itself was the intended target and was not the issue.

## Files

- `experiments/results/qwen36_v10_limit20_20260428/skill_call_agent_metrics.csv`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics.json`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics_report.md`

## Actions

- Changed primary `skill_call_evidence_avg` to use `cases_with_skill_call_evidence` as the denominator.
- Kept the previous all-planned denominator as `skill_call_evidence_avg_per_planned_case`.
- Changed primary `trace_skill_records_followup_new_avg` and `native_skill_call_events_avg` to the same nonzero-denominator convention.
- Kept planned-case variants for audit comparison.
- Updated definitions and the report table so the primary table now presents `Avg / evidence case`.

## Verification

- Recomputed all aggregate rows from `skill_call_case_metrics.csv`.
- Confirmed primary trace-record evidence averages now exclude zero-evidence cases.

## Result

The result files now use the expected `avg` denominator: only cases where the corresponding evidence appears. The trace-record evidence count remains the primary injected skill-loop evidence statistic.
