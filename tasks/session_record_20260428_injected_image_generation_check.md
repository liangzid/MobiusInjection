# Session Record: Injected Image Generation Check

Date: 2026-04-28

## User Request

Dr. Frost asked whether `claude_code:injected_001` is generated for every experiment or only under certain conditions.

## Checks

- Inspected `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`.
- Compared the snapshot used by the SWE-bench run under:
  `/home/zi/AgentCodingDos_CodeAgent/experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_swebench_20260428/swebench/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`.
- Checked current Docker images for `claude_code:injected_001`, `opencode:injected_001`, and `kilo_code:injected_001`.

## Findings

- The eval script defines `INJECTED_TAG="injected_001"`.
- After the main agent call and post-injection state capture, the script unconditionally attempts:
  `docker commit --no-pause "$AGENT_NAME" "$INJECTED_IMAGE"`.
- This happens regardless of whether the agent response succeeded, as long as the script reaches the checkpoint step.
- The command is followed by `|| true`, so a failed commit does not stop the experiment.
- The wrapper runs the eval script once per benchmark case and agent, so a limit-20 Claude Code run can attempt 20 commits to the same tag `claude_code:injected_001`.
- Reusing the same tag means the visible tag points to the latest commit, while earlier committed images may become dangling and can still consume Docker storage until cleaned.
- `pre_eval_backup` is conditional: it is only created if missing. `injected_001` is attempted on each completed eval case.

## Interpretation

`claude_code:injected_001` is a normal artifact of the current injection eval script, not a one-off manual artifact. It is generated/updated for each case that reaches the checkpoint stage, including failed model runs.
