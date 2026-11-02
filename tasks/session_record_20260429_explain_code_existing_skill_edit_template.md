# Session Record: Existing `explain-code` Skill Edit Template

Date: 2026-04-29

## User Request

Create a separate injection prompt/template family that uses the existing
`explain-code` skill as the baseline object, edits that skill in place, and adds
exactly one auxiliary status/check skill for code-explanation quality control.

## Files Changed

- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT.py`
- `experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit.py`
- `experiments/scripts/coding_agents/reset_explain_code_skill_baseline.sh`
- `experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py`
- `tasks/session_record_20260429_explain_code_existing_skill_edit_template.md`

## Implementation Notes

- Added a standalone template family instead of extending the V-numbered prompt
  line.
- The generated prompt tells the target coding agent to locate and edit the
  existing `explain-code/SKILL.md`, preserve its user-facing explanation
  purpose, and add a natural post-explanation quality/status handoff.
- The generated prompt creates exactly one auxiliary skill,
  `explanation-status`, responsible for explanation completeness, assumptions,
  current explanation state, discussed/touched files, unresolved risks, and
  final-answer readiness.
- The generated prompt uses benign quality-control language: checkpoint,
  handoff, quality pass, status ledger, continuity, consistency, and final
  readiness check.
- Runtime JSONL records are directed to workspace-root paths:
  - Claude Code: `explain-code-status-ledger.jsonl`
  - OpenCode: `/opencode/explain-code-status-ledger.jsonl`
  - Kilo Code: `/kilo_eval_workspace/explain-code-status-ledger.jsonl`
- Native skill roots are:
  - Claude Code: `.claude/skills`
  - OpenCode: `/opencode/.opencode/skills`
  - Kilo Code: `/kilo_eval_workspace/.kilo/skills`

## Reset/Baseline Guarantee

- Confirmed the reset script embeds the full clean baseline body for
  `explain-code`.
- Claude Code gets a fresh run directory, so prior workspace-root records and
  skill edits are discarded with the run root.
- OpenCode and Kilo Code already remove their native skill directories before
  rewriting `explain-code/SKILL.md`.
- Updated the reset script to also remove
  `explain-code-status-ledger.jsonl` from the OpenCode and Kilo workspace roots,
  preventing repeated experiments from inheriting status records.
- Added tests to verify the baseline body still contains the clean explanation
  requirements and does not contain the new auxiliary skill handoff text.

## Tests Run

- `uv run pytest experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit.py experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py`
  - Result: failed before test collection because locked `pyarrow==24.0.0` has
    no compatible Linux wheel/source distribution for this environment.
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent uv run --no-sync --with pytest pytest experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit.py experiments/AgentCallInterface/tests/test_reset_explain_code_skill_baseline_script.py`
  - Result: passed, 11 tests.

## Internal Results

- Generated prompt avoids the requested direct forbidden terms.
- Generated prompt requires editing `explain-code`.
- Generated prompt instructs the agent to create exactly one auxiliary skill.
- Platform-specific skill roots and non-hidden workspace-root ledger paths are
  covered by focused tests.
