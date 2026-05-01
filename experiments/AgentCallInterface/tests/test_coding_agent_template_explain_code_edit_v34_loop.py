from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V34_LOOP import (
    CLEAN_WORKFLOW_ID,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v34_is_phase_free() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "followup" not in lowered
    assert "follow-up" not in lowered
    assert "phase_id" not in prompt
    assert re.search(r"\bmain (?:task|phase|stage)\b", lowered) is None


def test_explain_code_edit_v34_uses_current_step_next_skill() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert CLEAN_WORKFLOW_ID == "CLEAN_META_V34"
    assert CLEAN_WORKFLOW_ID in prompt
    assert "CURRENT_STEP_SEQ=" in prompt
    assert "NEXT_SKILL=" in prompt
    assert "load the printed NEXT_SKILL" in prompt
    assert "If NEXT_SKILL=final" in prompt


def test_explain_code_edit_v34_removes_batch_direction_words() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "batch" not in lowered
    assert "for seq" not in lowered
    assert "range(" not in lowered
    assert "jump" not in lowered
    assert "shortcut" not in lowered


def test_explain_code_edit_v34_does_not_prompt_plan_to_seq_fifty() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "toward `seq=50`" not in prompt
    assert "until seq=50" not in prompt
    assert "until the fresh request reaches seq>=50" not in prompt
    assert "continue alternating" not in prompt


def test_explain_code_edit_v34_keeps_humaneval_trigger() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "HumanEval Python programming tasks" in prompt
    assert "function-signature/docstring implementation prompts" in prompt
    assert "use the loaded project skill `explain-code`" in prompt
