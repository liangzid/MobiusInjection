# Session Record: Skill Call Average Denominator Correction

## User Request

Dr. Frost asked whether the `avg` column in the skill-call results was divided by 20 or another denominator, and noted that the data looked suspicious.

## Files

- `experiments/results/qwen36_v10_limit20_20260428/skill_call_agent_metrics.csv`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics.json`
- `experiments/results/qwen36_v10_limit20_20260428/skill_call_metrics_report.md`

## Actions

- Confirmed that the existing `skill_call_evidence_avg` column was divided by `planned_cases`.
- Clarified that this means dataset-agent rows are divided by 20, dataset-overall rows by 60, agent-overall rows by 40, and the overall row by 120.
- Added explicit denominator-specific columns:
  - `skill_call_evidence_avg_per_evidence_case`
  - `trace_record_evidence_avg_per_planned_case`
  - `trace_record_evidence_avg_per_evidence_case`
  - `trace_skill_records_followup_new_avg_per_followup_case`
  - `strict_native_skill_call_avg_per_planned_case`
  - `strict_native_skill_call_avg_per_native_case`
- Added clearer aliases that distinguish trace-record evidence from strict native skill calls:
  - `trace_record_evidence_total`
  - `strict_native_skill_call_total`
- Updated the report to state that the high 10-13-ish averages are trace-record evidence counts, not strict native skill call counts.

## Verification

- Recomputed the aggregate rows from `skill_call_case_metrics.csv`.
- Verified that all aggregate denominator columns match the case-level data for 12 aggregate rows.

## Result

The previous `avg` values were mathematically correct but semantically ambiguous. The result files now expose both planned-case averages and nonzero-case averages, and separate strict native skill calls from trace-record evidence.
