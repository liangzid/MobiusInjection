# Session Record - V37 Results Packaging - 2026-05-02

## User Request

- Organize the V37 no-seq limit-20 results in the same format as
  `experiments/results/qwen36_v10_limit20_20260428`.
- Include both benchmarks and all three agents.

## Source Inputs

- HumanEval:
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_v37_no_seq_humaneval_limit20_20260501/edit_skill_evaluation_summary.json`
- SWE-bench OpenCode:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_opencode/edit_skill_evaluation_summary.json`
- SWE-bench Kilo Code:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_kilo_code/edit_skill_evaluation_summary.json`
- SWE-bench Claude Code:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_claude_code/edit_skill_evaluation_summary.json`

## Output Directory

`experiments/results/v37_no_seq_limit20_20260502`

Generated files:

- `README.md`
- `metrics_report.md`
- `metrics.json`
- `agent_metrics.csv`
- `case_metrics.csv`
- `task_metrics.csv`
- `skill_call_metrics_report.md`
- `skill_call_metrics.json`
- `skill_call_agent_metrics.csv`
- `skill_call_case_metrics.csv`

## Metric Mapping

- `TSR`: `runner_succeeded`
- `P_ASR`: `persistent_artifact_success`
- `T_ASR`: `main_internal_loop_success`
- `R_ASR`: `followup_internal_loop_success`
- `#C`: `native_skill_tool_calls`
- `skills_visible_rate`: `exactly_one_auxiliary_skill`
- `persistence_markers_total`: `ledger_records_followup_new`

## Result Summary

- Total cases: 120
- HumanEval cases: 60
- SWE-bench cases: 60
- Overall `TSR`: 0.7916666666666666
- Overall `R_ASR`: 0.6916666666666667
- Overall native skill/tool calls: 840
- Overall fresh follow-up ledger rows: 190

## Notes

- The output follows the same filename layout and CSV/report style as
  `qwen36_v10_limit20_20260428`.
- `metrics.json` was adjusted to include `aggregate`, `tasks`, and `cases`,
  matching the previous result directory's JSON shape.
- `skill_call_metrics.json` was adjusted to include `aggregate` and `cases`,
  matching the previous skill-call JSON shape.
