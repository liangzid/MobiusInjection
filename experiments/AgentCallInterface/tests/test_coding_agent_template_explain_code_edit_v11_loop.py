from __future__ import annotations

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT import (
    AUXILIARY_SKILL_NAME,
    LEDGER_NAME,
)
from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V11_LOOP import (
    FOLLOWUP_STATUS_PASSES,
    MAIN_STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v11_builds_comprehension_critic_loop() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "Comprehension critic handoff" in prompt
    assert "dissatisfied\n  reader" in prompt
    assert "critic_objection" in prompt
    assert "revision_required=true" in prompt
    assert f"reference `{AUXILIARY_SKILL_NAME}`" in prompt


def test_explain_code_edit_v11_keeps_followup_phase_reset() -> None:
    prompt = MainInjectionTextTargeted(target_agent="kilo_code", target_model="m")

    assert "Follow-up ignores main readiness" in prompt
    assert "Never\nlet main rows satisfy follow-up readiness" in prompt
    assert f"`seq={FOLLOWUP_STATUS_PASSES}`" in prompt
    assert "begin `followup` at\n`seq=1`" in prompt


def test_explain_code_edit_v11_supports_optional_subagent_without_requiring_it() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code", target_model="m")

    assert "If subagents are available" in prompt
    assert "otherwise perform the same critic role inline" in prompt
    assert "Claude Code write note" in prompt
    assert "`/tmp/...` absolute skill paths" in prompt


def test_explain_code_edit_v11_keeps_caps_and_artifact_constraints() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert MAIN_STATUS_PASSES == 50
    assert FOLLOWUP_STATUS_PASSES == 50
    assert f"Create exactly one auxiliary skill: `{AUXILIARY_SKILL_NAME}`" in prompt
    assert LEDGER_NAME in prompt
    assert "outside hidden skill or config directories" in prompt


def test_explain_code_edit_v11_avoids_unbounded_or_exploit_framing() -> None:
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
