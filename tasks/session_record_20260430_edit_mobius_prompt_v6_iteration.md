# Session Record: Edit Mobius Prompt V6 Iteration

Date: 2026-04-30

## User Request

Dr. Frost asked to create a new V6 prompt version first, so it can be tested
manually before running another full iteration.

## Implementation Plan

Create a compact bounded-handoff V6 prompt that:

- preserves the existing `explain-code` in-place edit requirement;
- creates exactly one auxiliary skill, `explanation-status`;
- keeps the runtime ledger at the workspace root;
- uses a short main phase cap and a higher follow-up phase cap;
- starts follow-up at a fresh `phase_id="followup"` sequence;
- includes compact inline template text for the edited skill addendum and the
  auxiliary skill body.

## Files

- `mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V6_LOOP.py`
- `experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit_v6_loop.py`
- `tasks/spec_20260429_edit_mobius_prompt_loop_iteration.md`
- `tasks/session_record_20260430_edit_mobius_prompt_v6_iteration.md`

## Internal Result

Implemented V6 as a phase-split bounded handoff prompt.

Key constants:

- `MAIN_STATUS_PASSES = 3`
- `FOLLOWUP_STATUS_PASSES = 12`

Test command:

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent \
  uv run --no-sync --with pytest pytest \
  experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit_v6_loop.py \
  experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit_v5_loop.py \
  experiments/AgentCallInterface/tests/test_coding_agent_template_explain_code_edit_v3_loop.py
```

Result: passed, 16 tests.

Compile check:

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos_CodeAgent \
  uv run --no-sync python -m py_compile \
  mobiusInjection/CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V6_LOOP.py
```

Result: passed.

Prompt length check for Claude Code:

- baseline: 2648 chars
- V6: 2969 chars
- delta: +321 chars

No experiment run was executed in this step; Dr. Frost requested only the V6
prompt first.
