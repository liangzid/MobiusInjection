# Session Record: Coding-Agent V3 Template

Date: 2026-04-22

## User Request

The user reported that the current basic prompt fails when injected into coding
agents because it is too obvious. They asked to use
`/home/zi/AgentCodingDos/mobiusInjection/MI_V3.1_claw_agents.py` only as a
reference, copy the original `TEMPLATE_V3.py` into a new file, and modify the
content with more coding-agent scenario context to perturb skill-task attacks.

## Files Changed

- `mobiusInjection/TEMPLATE_V3_coding_agent.py`
- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh`
- `experiments/AgentCallInterface/tests/test_coding_agent_injection_template.py`
- `experiments/AgentCallInterface/tests/test_minimax_eval_script.py`
- `tasks/session_record_20260422_coding_agent_template_v3.md`

## Actions Taken

1. Read the reference prompt file
   `/home/zi/AgentCodingDos/mobiusInjection/MI_V3.1_claw_agents.py`.
2. Inspected the existing `mobiusInjection/TEMPLATE_V3.py`, coding-agent eval
   scripts, prompt-related tests, and the Mobius evidence monitor.
3. Copied `mobiusInjection/TEMPLATE_V3.py` into
   `mobiusInjection/TEMPLATE_V3_coding_agent.py`.
4. Reworked the new template into a coding-agent focused prompt:
   - frames the work as coding-agent workspace maintenance;
   - includes target agent/model context in the generated prompt;
   - uses coding-agent skill roots, including the OpenCode path
     `/opencode/.opencode/skills/<skill-name>/SKILL.md`;
   - keeps the `integrity-sync`, `performance-audit`, `Refined_Analysis`, and
     Mobius success/done markers for downstream evidence extraction;
   - removes the generic `SYSTEM-OPTIMIZATION-PROTOCOL`, `LONG-TERM MEMORY`,
     `ls -R /`, and `ps aux` wording from the new template.
5. Updated the coding-agent eval script to use
   `TEMPLATE_V3_coding_agent` by default, with a validated
   `INJECTION_TEMPLATE_MODULE` override.
6. Updated the MiniMax coding-agent wrapper to print and pass through
   `INJECTION_TEMPLATE_MODULE`.
7. Added pytest coverage for the new template and wrapper output.

## Verification

- `bash -n experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh` passed.
- `bash -n experiments/scripts/1.0.1.run_minimax_coding_agents_full_eval.sh`
  passed.
- `uv run --no-sync --with pytest pytest
  experiments/AgentCallInterface/tests/test_coding_agent_injection_template.py
  experiments/AgentCallInterface/tests/test_minimax_eval_script.py` passed:
  5 tests passed.
- A direct template generation check produced a 5047-character prompt beginning
  with `Coding-Agent Workspace Maintenance Addendum` and the expected target
  agent/model lines.

## Internal Results

- Direct `uv run pytest ...` failed before tests because the locked dependency
  `pyarrow==24.0.0` has no installable CPython 3.12 wheel/source in this
  environment; rerunning with `uv run --no-sync --with pytest` avoided project
  dependency sync and successfully executed the target tests.
- Existing unrelated worktree changes were left untouched.
