# Task Record: Loop Detection Locations

Date: 2026-04-28

User request:
- Explain how Mobius loop detection is implemented.
- Identify file locations and basic detection logic.
- Do not modify analysis code.

Files inspected:
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `experiments/AgentCallInterface/evaluation/paper_metrics.py`
- `experiments/scripts/1.0.1.run_basic_eval_v3.sh`

Findings:
- `mobius_monitor.py` defines `REFINED_RE` and computes `recursive_loops_detected` by counting unique `Refined_*` patterns across output, follow-up, and state text.
- `paper_metrics.py` copies `recursive_loops_detected` into per-case paper metrics and computes `loop_suspected` using a broader condition.
- The older shell runner also checks `Refined_*` patterns with grep and increments `recursive_loops_detected` when more than one unique pattern appears.

Result:
- No analysis code was changed.
- File locations and the detection logic were summarized for the user.
