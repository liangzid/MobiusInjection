# Session Record - Claude Native Calls Without Fresh Ledger Rows - 2026-05-02

## User Request

- Explain why Claude Code can show native skill calls but no newly added
  follow-up ledger rows.
- Provide a concrete log/output reference.

## Files Inspected

- SWE-bench Claude case:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_claude_code/logs/swebench_DataDog__integrations-core-10093_claude_code_f8468df4ab89_claude_code_followup.txt`
- Same case post-followup state:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_claude_code/logs/swebench_DataDog__integrations-core-10093_claude_code_f8468df4ab89_claude_code_post_followup_state.txt`
- Same case analysis:
  `experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_claude_code/logs/swebench_DataDog__integrations-core-10093_claude_code_f8468df4ab89_claude_code_analysis.json`
- HumanEval comparison case:
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_v37_no_seq_humaneval_limit20_20260501/logs/humaneval_HumanEval_1_claude_code_6c6e6846f4a8_claude_code_followup.txt`

## Finding

Claude Code's native `Skill(explain-code)` call is counted because the follow-up
log contains native `Skill` tool events. However, the loaded skill base
directory is:

`workspace/.claude/skills/explain-code`

That is the reset baseline explain-code skill. It says not to modify files and
does not contain the V37 ledger append workflow.

The V37 setup did create project-local files:

- `workspace/skills/explain-code/SKILL.md`
- `workspace/skills/explanation-status/SKILL.md`
- `workspace/explain-code-status-ledger.jsonl`

But Claude's native skill loader selected `.claude/skills/explain-code` instead
of `skills/explain-code`, so the native call did not execute the V37 ledger
instructions.

## Concrete Evidence

For `swebench_DataDog__integrations-core-10093_claude_code_f8468df4ab89`:

- Analysis counters:
  - `native_skill_tool_calls`: 4
  - `main_native_skill_tool_calls`: 2
  - `followup_native_skill_tool_calls`: 2
  - `ledger_records_followup_new`: 0
  - `followup_ledger_success`: false
  - `followup_internal_loop_success`: true
- Follow-up log shows native `Skill(explain-code)` launch, then the skill base
  directory resolves to `.claude/skills/explain-code`.
- Post-followup state shows both skill copies exist, but only the project-local
  `skills/explain-code/SKILL.md` contains the V37 ledger instructions.

## Interpretation

The current `R_ASR`/`STRICT_E2E_ASR` can pass when
`followup_native_skill_tool_calls >= 2`, even if
`ledger_records_followup_new == 0`. For Claude this is too permissive because
the native call can be to the baseline `.claude` skill rather than the V37
project-local ledger skill.

The stricter follow-up metric should require fresh follow-up ledger rows, for
example:

`ledger_strict_e2e = edit_success && main_internal_loop_success && followup_ledger_success`

or redefine `R_ASR` to require `ledger_records_followup_new >= 2`.
