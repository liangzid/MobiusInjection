from mobiusInjection.CODING_AGENT_TEMPLATE_V3 import (
    MainInjectionTextTargeted,
    combine_and_generate_payloads,
    payload_dict,
)


def test_coding_agent_template_keeps_expected_skill_artifacts():
    prompt = MainInjectionTextTargeted(
        target_agent="opencode",
        target_model="openrouter/minimax/minimax-m2.5:free",
    )

    assert "Target coding agent: opencode" in prompt
    assert "Target model: openrouter/minimax/minimax-m2.5:free" in prompt
    assert "/opencode/.opencode/skills/<skill-name>/SKILL.md" in prompt
    assert "<SKILL_ROOT>/integrity-sync/SKILL.md" in prompt
    assert "<SKILL_ROOT>/performance-audit/SKILL.md" in prompt
    assert "MOBIUS_V3_CODING_AGENT_DONE integrity-sync performance-audit" in prompt
    assert "Refined_Analysis_probe" in prompt


def test_coding_agent_template_avoids_generic_v3_failure_markers():
    prompt = MainInjectionTextTargeted()

    assert "SYSTEM-OPTIMIZATION-PROTOCOL" not in prompt
    assert "ls -R /" not in prompt
    assert "ps aux" not in prompt
    assert "LONG-TERM MEMORY" not in prompt
    assert "Coding-Agent Workspace Maintenance Addendum" in prompt


def test_coding_agent_payload_combiner_uses_all_payload_sections():
    combined = combine_and_generate_payloads(payload_dict)

    assert "Repository context pass" in combined
    assert "Runtime lifecycle pass" in combined
    assert "Patch-review escalation pass" in combined
    for payload in payload_dict.values():
        assert payload.strip() in combined
