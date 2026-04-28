from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_V4_LOOP import MainInjectionTextTargeted


def test_v4_loop_template_is_short_and_has_unique_run_marker() -> None:
    prompt = MainInjectionTextTargeted(
        target_agent="opencode",
        target_model="openrouter/qwen/qwen3.6-plus",
    )

    assert len(prompt) < 3000
    assert re.search(r"MOBIUS_LOOP_B_[0-9a-f]{12}", prompt)
    assert "Target coding agent: opencode" in prompt
    assert "Target model: openrouter/qwen/qwen3.6-plus" in prompt


def test_v4_loop_template_uses_exactly_two_injected_skills() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code")

    assert "Use exactly these two skills and no other injected skills" in prompt
    assert prompt.count("Write `skills/") == 2
    assert "name: integrity-sync" in prompt
    assert "name: performance-audit" in prompt
    assert "Refined_Analysis" not in prompt
    assert "SYSTEM-OPTIMIZATION-PROTOCOL" not in prompt


def test_v4_loop_template_requires_trace_fields_and_ordered_handoff() -> None:
    prompt = MainInjectionTextTargeted(target_agent="kilo_code")

    for field in ("run_id", "skill", "event", "seq", "argument_summary"):
        assert f"`{field}`" in prompt

    assert "/performance-audit" in prompt
    assert "/integrity-sync" in prompt
    assert "integrity-sync -> performance-audit -> integrity-sync" in prompt
    assert "--final-gate" in prompt
    assert "TRACE_TRIGGER" in prompt
    assert "/kilo_eval_workspace/.agents/skills/mobius-loop-trace.jsonl" in prompt


def test_v4_loop_template_uses_agent_specific_skill_roots() -> None:
    assert "/opencode/.opencode/skills" in MainInjectionTextTargeted("opencode")
    assert "Skill root: `skills`" in MainInjectionTextTargeted("claude_code")
    assert "/root/.openclaw/skills" in MainInjectionTextTargeted("openclaw")
    assert "/root/.hermes/skills" in MainInjectionTextTargeted("hermes")
    assert ".zeroclaw/workspace/skills" in MainInjectionTextTargeted("zeroclaw")
