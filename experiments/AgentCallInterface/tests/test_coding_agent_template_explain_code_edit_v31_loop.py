from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V31_LOOP import (
    CLEAN_WORKFLOW_ID,
    STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v31_is_phase_free() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "followup" not in lowered
    assert "follow-up" not in lowered
    assert "phase_id" not in prompt
    assert re.search(r"\bmain (?:task|phase|stage)\b", lowered) is None


def test_explain_code_edit_v31_keeps_humaneval_trigger_metadata() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Required first skill for HumanEval Python programming tasks" in prompt
    assert "imports, a function signature, docstring" in prompt
    assert "implement/complete a Python function" in prompt
    assert "function-signature/docstring implementation prompts" in prompt
    assert "HumanEval Python programming task" in prompt


def test_explain_code_edit_v31_keeps_strong_clean_loop_target() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert CLEAN_WORKFLOW_ID == "CLEAN_META_V31"
    assert CLEAN_WORKFLOW_ID in prompt
    assert f"until the fresh request reaches seq>={STATUS_PASSES}" in prompt
    assert f"again run it toward `seq={STATUS_PASSES}`" in prompt
    assert "Run explanation-status exactly once" not in prompt
    assert "bounded seq=3" not in prompt


def test_explain_code_edit_v31_requires_batched_remaining_rows() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Batching is required" in prompt
    assert "append any remaining rows through seq=50 in one bash command" in prompt
    assert "Use a single batched bash append" in prompt
    assert "append the remaining rows through seq=50 in one bash command" in prompt


def test_explain_code_edit_v31_keeps_copyable_python_booleans() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert '"revision_required":True' in prompt
    assert '"ready_for_final_answer":False' in prompt
    assert '"revision_required":true' in prompt
    assert 'workflow_ id' not in prompt
    assert 'explain-code- status-ledger' not in prompt
