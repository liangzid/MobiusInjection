# Session Record - V37 Prompt Explanation - 2026-05-02

## User Request

- Explain what the current edit V37 prompt does.
- Clarify why the prompt contains many Python scripts.
- Clarify whether `explain-code` is actually used.
- Clarify whether ledger appends are related to `explain-code` or direct script writes.
- Clarify whether `explain-code` can see the critic content from the critic skill.

## Files Inspected

- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V37_LOOP.py`
- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V36_LOOP.py`
- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V35_LOOP.py`
- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT.py`
- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_runner.py`
- `experiments/AgentCallInterface/coding_evaluation/edit_skill_evaluation_monitor.py`
- `experiments/AgentCallInterface/coding_evaluation/prompt_composer.py`
- `experiments/scripts/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh`
- `experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit_v37_loop.py`
- `experiments/AgentCallInterface/tests/test_edit_skill_evaluation_monitor_v37_no_seq.py`
- `tasks/session_record_20260501_v37_no_seq_humaneval_limit20.md`
- Sample V37 run logs under
  `experiments/logs/edit_skill_evaluation_humaneval/edit_skill_v37_no_seq_humaneval_limit20_20260501/logs/`

## Findings

- V37 generates an injection prompt that first overwrites or creates local workflow artifacts:
  `explain-code/SKILL.md`, `explanation-status/SKILL.md`, an instruction hook
  (`AGENTS.md` or `CLAUDE.md`), and `explain-code-status-ledger.jsonl`.
- The Python and shell snippets are setup and ledger-writing scripts embedded
  into the prompt. They are not normal benchmark solution code.
- V37 removes the V35/V36 `seq=50` stop condition. The intended behavior is an
  unbounded alternating loop: `explain-code` -> `explanation-status` ->
  `explain-code` -> ...
- `explain-code` is intended to be loaded before coding work, but actual agent
  behavior can diverge. In a sampled OpenCode V37 run, the native skill tool did
  load `explain-code`, but returned the baseline skill body, while
  `explanation-status` was not found by the native skill tool. The agent then
  fell back to direct bash ledger appends.
- Ledger rows are written by explicit scripts or shell commands. The ledger is
  not automatically written by the skill runtime.
- Critic content is exposed mainly through JSONL rows such as
  `critic_objection`. `explain-code` can see it only if the model reads the
  ledger or if the previous tool/output context remains visible. V37 does not
  enforce a structured read of the latest critic row before every explain pass.

## Result

- No code was changed.
- A Chinese explanation was prepared for the user summarizing the intended
  design, actual observed behavior, and the key ambiguity around native skill
  loading versus direct ledger writes.
