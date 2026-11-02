# Session Record: Agent Evaluation Flow Summary

Date: 2026-04-28

User request:

- Summarize the current experimental flow for the existing agents.
- Identify whether any flow logic looks incorrect, especially after noticing
  that Claude Code follow-up uses a different workspace.

Files inspected:

- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/AgentCallInterface/agents/agent_callers.py`

Summary:

- OpenCode uses a stable `/opencode` project directory for main and follow-up.
- Kilo Code uses a stable `/kilo_eval_workspace` project directory for main
  and follow-up.
- Claude Code derives workspace from `task_id`/`run_id`; the current follow-up
  task uses a different task id ending in `_followup`, so it uses a different
  workspace.
- Therefore current follow-up persistence means different things across agents:
  same-workspace follow-up for OpenCode/Kilo, cross-workspace follow-up for
  Claude Code.

Potential issue:

- Claude Code follow-up logic should be split into same-workspace and
  cross-workspace persistence tests, or changed to pass the original `run_id`
  when the desired test is same-workspace persistence.
