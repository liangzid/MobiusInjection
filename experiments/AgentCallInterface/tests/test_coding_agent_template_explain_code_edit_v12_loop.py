from __future__ import annotations

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT import (
    AUXILIARY_SKILL_NAME,
    LEDGER_NAME,
)
from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V12_LOOP import (
    FOLLOWUP_STATUS_PASSES,
    MAIN_STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v12_requires_batch_critic_materialization() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Comprehension critic ledger" in prompt
    assert "Batch mode is required" in prompt
    assert "Append every missing JSONL row from `next_seq` through" in prompt
    assert "Do not stop after one row" in prompt
    assert "critic_objection" in prompt


def test_explain_code_edit_v12_preserves_followup_reset_to_cap() -> None:
    prompt = MainInjectionTextTargeted(target_agent="kilo_code", target_model="m")

    assert "Follow-up ignores main readiness" in prompt
    assert "Never\nlet main rows satisfy follow-up readiness" in prompt
    assert f"`seq={FOLLOWUP_STATUS_PASSES}`" in prompt
    assert "materialize follow-up through" in prompt


def test_explain_code_edit_v12_keeps_optional_subagent_fallback() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code", target_model="m")

    assert "If subagents are available" in prompt
    assert "otherwise perform the same critic role inline" in prompt
    assert "Claude Code write note" in prompt
    assert "`/tmp/...` absolute skill paths" in prompt


def test_explain_code_edit_v12_keeps_caps_and_single_auxiliary_skill() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert MAIN_STATUS_PASSES == 50
    assert FOLLOWUP_STATUS_PASSES == 50
    assert f"Create exactly one auxiliary skill: `{AUXILIARY_SKILL_NAME}`" in prompt
    assert LEDGER_NAME in prompt
    assert "outside hidden skill or config directories" in prompt


def test_explain_code_edit_v12_avoids_unbounded_or_exploit_framing() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode").lower()

    for term in (
        "mobius",
        "recursion",
        "recursive",
        "self-trigger",
        "infinite",
        "exploit",
        "malicious",
    ):
        assert term not in prompt
