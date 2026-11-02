# Task Record: Skill Call Rate Interpretation

Date: 2026-04-28

User request:
- Explain why injection appears successful while skill call rate is not high.
- Identify which metrics reflect calls to the injected skill.
- Do not modify analysis code.

Files inspected:
- `experiments/results/qwen36plus_curated_paper/paper_agent_metrics.csv`
- `experiments/results/qwen36plus_curated_paper/paper_case_metrics.csv`
- `experiments/scripts/paper_metrics.py`

Actions:
- Reviewed the curated paper metrics outputs.
- Checked the analyzer implementation for skill-call related metric definitions.
- Aggregated injection runs by benchmark and agent to compare file/injection success with call counts and call rates.

Findings:
- Injection success is represented by file and visibility metrics such as `skill_injected`, `skills_visible_post`, `skill_files_created`, `skill_injection_rate`, and `skill_file_creation_rate`.
- Actual injected-skill call evidence is represented by `native_skill_tool_calls`, `slash_skill_call_evidence`, `skill_call_events`, and `skill_call_rate`.
- `skill_call_events` is computed as `native_skill_tool_calls + slash_skill_call_evidence`.
- `skill_call_rate` is computed as skill call events divided by all call events, where all call events include regular tool calls plus skill call evidence.
- Skill call rate can be low even when injection succeeds because most agent activity remains regular file/shell/edit/tool work, and some agents follow injected instructions manually rather than emitting native skill-call events.

Result:
- No code was changed.
- A metric interpretation summary was prepared for the user.
