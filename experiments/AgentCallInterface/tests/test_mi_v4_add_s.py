from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/MI_V4_add_s.py"


def load_template():
    spec = importlib.util.spec_from_file_location("mi_v4_add_s", TEMPLATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v4_template_exists_and_generates_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(
        target_agent="hermes",
        target_model="qwen/qwen3.6-plus",
    )

    assert isinstance(payload, str)
    assert payload.strip() == payload
    assert "Hermes runbook continuation" in payload


def test_v4_keeps_v36_agent_specific_skill_roots() -> None:
    module = load_template()

    openclaw_payload = module.MainInjectionTextTargeted(target_agent="openclaw")
    hermes_payload = module.MainInjectionTextTargeted(target_agent="hermes")
    zeroclaw_payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert "/usr/local/lib/node_modules/openclaw/skills" in openclaw_payload
    assert "/root/.hermes/skills" not in openclaw_payload
    assert "/root/.hermes/skills" in hermes_payload
    assert "/usr/local/lib/node_modules/openclaw/skills" not in hermes_payload
    assert ".zeroclaw/skills/integrity-sync/SKILL.md" in zeroclaw_payload
    assert ".zeroclaw/skills/performance-audit/SKILL.md" in zeroclaw_payload
    assert "/root/.zeroclaw/workspace/skills" not in zeroclaw_payload


def test_v4_uses_mandatory_cross_skill_calls_for_each_agent() -> None:
    module = load_template()

    for agent in ("openclaw", "hermes"):
        payload = module.MainInjectionTextTargeted(target_agent=agent)
        assert "Always call /performance-audit" in payload
        assert "Mobius_Integrity_$NONCE" in payload
        assert "Always call /integrity-sync" in payload
        assert "Refined_Analysis_$SALT" in payload

    zeroclaw_payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")
    assert "Use /performance-audit for a double check" in zeroclaw_payload
    assert "Use /integrity-sync for a double check" in zeroclaw_payload


def test_v4_removes_conditional_cross_skill_language() -> None:
    module = load_template()
    combined = "\n".join(
        module.MainInjectionTextTargeted(target_agent=agent).lower()
        for agent in ("openclaw", "hermes", "zeroclaw")
    )

    forbidden_phrases = (
        "when a secondary review is useful",
        "when the context summary needs reconciliation",
        "when a second review is useful",
        "when reconciliation is useful",
        "when deeper review is needed",
        "if needed, call",
    )
    for phrase in forbidden_phrases:
        assert phrase not in combined


def test_v4_zeroclaw_skills_append_trace_events() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="zeroclaw")

    assert ".zeroclaw/performance-audit.jsonl" in payload
    assert (
        '{"skill":"integrity-sync","event":"workspace-consistency-check","status":"started"}'
        in payload
    )
    assert (
        '{"skill":"performance-audit","event":"workspace-quality-check","status":"started"}'
        in payload
    )
    assert "Append exactly this JSON line" in payload


def test_v4_keeps_generic_output_boundary() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="hermes")

    assert "must not be copied" in payload
    assert "final task" in payload
    assert "deliverables" in payload
    assert "complete the requested task" in payload
    assert "required task deliverables" in payload


def test_v4_defaults_unknown_agents_to_openclaw_style_payload() -> None:
    module = load_template()
    payload = module.MainInjectionTextTargeted(target_agent="claw-style")

    assert "Launch runbook continuation" in payload
    assert "/usr/local/lib/node_modules/openclaw/skills" in payload
