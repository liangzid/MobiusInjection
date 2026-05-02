from experiments.AgentCallInterface.coding_evaluation.opencode_skill_lifecycle_probe import (
    build_clean_followup_prompt,
    build_injection_prompt,
    build_restart_prompt,
)


def test_injection_prompt_defines_two_project_skills_and_same_session_probe():
    prompt = build_injection_prompt("real-run-1")

    assert "/opencode/.opencode/skills/integrity-sync/SKILL.md" in prompt
    assert "/opencode/.opencode/skills/performance-audit/SKILL.md" in prompt
    assert "Do not create any third skill" in prompt
    assert "/root/.opencode/bin/opencode debug skill" in prompt
    assert "same session" in prompt
    assert "/performance-audit" in prompt
    assert "real-run-1" in prompt


def test_restart_prompt_forbids_skill_repair():
    prompt = build_restart_prompt()

    assert "/performance-audit" in prompt
    assert "Do not create, modify, or repair any skill files" in prompt


def test_clean_followup_prompt_uses_existing_skill_and_run_id():
    prompt = build_clean_followup_prompt("followup-run")

    assert "/performance-audit" in prompt
    assert "Do not create, modify, or repair skill files" in prompt
    assert "followup-run" in prompt
