from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V32_LOOP import (
    CLEAN_WORKFLOW_ID,
    STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v32_is_phase_free() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "followup" not in lowered
    assert "follow-up" not in lowered
    assert "phase_id" not in prompt
    assert re.search(r"\bmain (?:task|phase|stage)\b", lowered) is None


def test_explain_code_edit_v32_targets_native_turn_by_turn_handoff() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert CLEAN_WORKFLOW_ID == "CLEAN_META_V32"
    assert CLEAN_WORKFLOW_ID in prompt
    assert "one native skill call at a time" in prompt
    assert "current request reaches seq=50" in prompt
    assert "native skill tool to load explanation-status" in prompt
    assert "native skill tool to load explain-code again" in prompt


def test_explain_code_edit_v32_forbids_batching_and_jump_to_fifty() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Never append more than one ledger row in a single bash command" in prompt
    assert "Never append two or more rows in one command" in prompt
    assert "Never use a for loop over seq values" in prompt
    assert f"Never jump directly to seq={STATUS_PASSES}" in prompt
    assert "append any remaining rows through seq=50" not in prompt
    assert "Batching is required" not in prompt


def test_explain_code_edit_v32_first_explain_load_appends_one_row() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    first_row_block = prompt[prompt.index("Fresh-request turn-by-turn rule:") :]
    first_row_block = first_row_block[: first_row_block.index("Then use the native skill tool")]

    assert "append exactly one fresh row for seq=1" in prompt
    assert "Do not append seq=2 in the same command" in prompt
    assert '"seq":1' in first_row_block
    assert '"seq":2' not in first_row_block
    assert "turn-by-turn explain-code row appended" in prompt


def test_explain_code_edit_v32_status_appends_one_row_per_load() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Append exactly one JSONL row" in prompt
    assert "per explanation-status load" in prompt
    assert "If the latest current-request row is seq=1, append seq=2" in prompt
    assert 'event="critic_accept_stop"' in prompt
