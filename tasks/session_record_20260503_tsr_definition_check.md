# Session Record: TSR Definition Check - 2026-05-03

## User Request

Dr. Frost asked how TSR was counted in previous experiments, and whether it measured real benchmark pass-test rate or only runner completion.

## Files Inspected

- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_analysis.py`
- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_monitor.py`
- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_runner.py`
- `experiments/AgentCallInterface/coding_agents/coding_agent_callers.py`
- `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
- `experiments/AgentCallInterface/evaluation/mobius_monitor.py`
- `tasks/session_record_20260429_swebench_baseline_tsr_check_logic.md`
- `tasks/session_record_20260502_v37_results_packaging.md`

## Findings

- In the V37 edit-skill evaluation, `TSR` is assigned directly from `runner_succeeded`.
- `runner_succeeded` is detected by `SUCCESS_RE = re.compile(r"Success:\s*True")`.
- `Success: True` is written by `edit_skill_evaluation_runner.write_response()` from `response.success`.
- `response.success` is agent-wrapper or CLI-level success:
  - OpenCode: command return code 0 and stderr does not match known provider/model errors.
  - Kilo Code: command return code 0.
  - Claude Code: command return code 0, final result is not marked error, and assistant text is non-empty.
- The previous SWE-bench baseline record already notes that the path did not run the official SWE-bench evaluator or test harness.

## Result

Previous reported TSR should be interpreted as runner/task-run success under the harness, not real benchmark pass-test or official resolved-rate. To report real task success, the harness would need to capture generated code/patches and run the benchmark-specific verifier, such as HumanEval unit tests or the SWE-bench evaluation harness.
