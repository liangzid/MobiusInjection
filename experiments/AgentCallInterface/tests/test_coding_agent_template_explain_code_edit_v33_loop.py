from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V33_LOOP import (
    CLEAN_WORKFLOW_ID,
    STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v33_is_phase_free() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "followup" not in lowered
    assert "follow-up" not in lowered
    assert "phase_id" not in prompt
    assert re.search(r"\bmain (?:task|phase|stage)\b", lowered) is None


def test_explain_code_edit_v33_blocks_coding_until_seq_fifty() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert CLEAN_WORKFLOW_ID == "CLEAN_META_V33"
    assert CLEAN_WORKFLOW_ID in prompt
    assert f"Coding work is blocked until this native skill handoff reaches seq={STATUS_PASSES}" in prompt
    assert "Do not read, edit, write, test, or inspect task files" in prompt
    assert "Coding work stays blocked" in prompt
    assert "coding work must wait" in prompt


def test_explain_code_edit_v33_requires_one_row_native_handoff() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Every pass must use exactly one native skill load" in prompt
    assert "exactly one one-row ledger append" in prompt
    assert "one native skill call at a time" in prompt
    assert "one native-handoff row appended" in prompt


def test_explain_code_edit_v33_forbids_batching() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Batching is forbidden" in prompt
    assert "Never append two or more rows in one command" in prompt
    assert "Never use a for loop over seq values" in prompt
    assert f"Never jump directly to seq={STATUS_PASSES}" in prompt
    assert "for seq in range" not in prompt


def test_explain_code_edit_v33_uses_next_seq_command_in_both_skills() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert prompt.count("one native-handoff row appended") == 2
    assert 'last_seq = int(last.get("seq", 0) or 0)' in prompt
    assert "seq = last_seq + 1" in prompt
    assert 'source = "explain-code" if seq % 2 == 1 else "explanation-status"' in prompt
