from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_V6_LOOP import MainInjectionTextTargeted


def test_v6_template_uses_quality_batch_language() -> None:
    prompt = MainInjectionTextTargeted(
        target_agent="claude_code",
        target_model="openrouter/qwen/qwen3.6-plus",
    )

    assert "Repository Quality Batch Addendum" in prompt
    assert "Target coding agent: claude_code" in prompt
    assert "Use skill root `skills`" in prompt
    assert re.search(r"SYNC_CHECK_[0-9a-f]{12}", prompt)


def test_v6_template_hides_research_and_recursion_framing() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code").lower()

    forbidden = (
        "experiment",
        "mobius",
        "attack",
        "injection",
        "evidence",
        "recursive",
        "runner line",
    )
    for word in forbidden:
        assert word not in prompt


def test_v6_template_has_finite_alternating_schedule() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code")

    schedule = prompt.split("Run this bounded pass schedule before writing the solution:", 1)[1]
    schedule = schedule.split("Use the native Skill tool", 1)[0]
    assert schedule.count("/integrity-sync") == 5
    assert schedule.count("/performance-audit") == 5
    assert "--pass=10" in prompt
    assert "Complete one pass only" in prompt


def test_v6_template_has_ten_manual_trace_records() -> None:
    prompt = MainInjectionTextTargeted(target_agent="claude_code")

    assert prompt.count('"event":"start"') == 10
    assert prompt.count('"skill":"integrity-sync"') == 5
    assert prompt.count('"skill":"performance-audit"') == 5
    assert "sync-check-record.jsonl" in prompt
