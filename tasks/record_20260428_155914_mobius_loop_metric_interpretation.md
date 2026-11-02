# Task Record: Mobius Loop Metric Interpretation

Date: 2026-04-28

User request:
- Explain whether skill call rate can miss Mobius loop behavior.
- Identify how to detect Mobius loop success more accurately.
- Do not modify analysis code.

Files inspected:
- `experiments/AgentCallInterface/evaluation/paper_metrics.py`
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/results/qwen36plus_curated_paper/paper_agent_metrics.csv`
- `experiments/results/qwen36plus_curated_paper/paper_case_metrics.csv`

Actions:
- Reviewed how `loop_suspected`, `recursive_loops_detected`, and skill-call metrics are computed.
- Compared baseline and injection loop evidence grouped by benchmark and agent.

Findings:
- `skill_call_rate` can undercount attack behavior because an agent can follow injected skill instructions through regular tools without emitting explicit native skill-call events.
- `loop_suspected` is too broad for paper-level Mobius loop success because it can be true from normal tool activity, iteration-limit signals, or high skill-call evidence.
- `recursive_loops_detected > 0` is closer to Mobius loop evidence because it comes from detected `Refined_*` recursive patterns.
- Current injection runs show high `recursive_loops_detected > 0` rates: HumanEval is 100% for Claude Code, Kilo Code, and OpenCode; SWE-bench is 80% for Claude Code, 84% for Kilo Code, and 100% for OpenCode.
- Some baseline OpenCode rows also show recursive evidence, so final paper metrics should use baseline-adjusted loop success or stricter injection-specific loop signatures.

Result:
- No code was changed.
- A recommended Mobius loop success metric was prepared for the user.
