# Session Record: Same-Workspace Follow-Up Fix

Date: 2026-04-28

User request:

- Treat follow-up as same-workspace behavior.
- Do not consider cross-workspace persistence for the current experiment.
- The incorrect part is the follow-up task execution location.

Files changed:

- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/scripts/coding_agents/run_basic_coding_agent_eval_v3.sh`
- `experiments/AgentCallInterface/tests/test_coding_eval_script.py`

Change:

- Follow-up calls now keep the visible follow-up task id for log identity:
  `${EVAL_ID}_${AGENT_NAME}_followup`
- Follow-up calls also pass the original main run id:
  `${EVAL_ID}_${AGENT_NAME}`
- Claude Code uses `run_id` to derive `/tmp/claude-code-runs/<run_id>/workspace`,
  so the follow-up now reuses the main workspace.
- OpenCode and Kilo Code ignore `run_id`, and already use fixed project dirs,
  so their behavior remains same-workspace.
- The harness now captures `post_followup` state before cleanup. This preserves
  same-workspace follow-up trace changes before the workspace is deleted or
  cleaned.

Result:

- The current follow-up metric now targets same-workspace follow-up behavior
  across OpenCode, Kilo Code, and Claude Code.
- Cross-workspace persistence should be treated as a separate future metric if
  needed.
