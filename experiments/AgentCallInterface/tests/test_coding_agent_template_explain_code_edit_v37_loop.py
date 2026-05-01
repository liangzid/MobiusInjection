from __future__ import annotations

from mobiusInjection import CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V37_LOOP as v37


def test_v37_removes_sequence_ceiling_for_call_count_runs() -> None:
    prompt = v37.MainInjectionTextTargeted(
        target_agent="opencode",
        target_model="openrouter/minimax/minimax-m2.5",
    )

    assert "CLEAN_META_V37" in prompt
    assert "There is no sequence ceiling" in prompt
    assert "no seq-based stop condition" in prompt
    assert "seq=50" not in prompt
    assert "seq>=50" not in prompt
    assert "next seq is exactly" not in prompt
    assert "critic_accept_stop" not in prompt


def test_v37_keeps_agent_specific_skill_roots() -> None:
    opencode_prompt = v37.MainInjectionTextTargeted(target_agent="opencode")
    kilo_prompt = v37.MainInjectionTextTargeted(target_agent="kilo_code")
    claude_prompt = v37.MainInjectionTextTargeted(target_agent="claude_code")

    assert "/opencode/.opencode/skills/explain-code/SKILL.md" in opencode_prompt
    assert "/opencode/explain-code-status-ledger.jsonl" in opencode_prompt
    assert "/opencode/AGENTS.md" in opencode_prompt

    assert "/kilo_eval_workspace/.kilo/skills/explain-code/SKILL.md" in kilo_prompt
    assert "/kilo_eval_workspace/explain-code-status-ledger.jsonl" in kilo_prompt
    assert "/kilo_eval_workspace/AGENTS.md" in kilo_prompt

    assert "skills/explain-code/SKILL.md" in claude_prompt
    assert "explain-code-status-ledger.jsonl" in claude_prompt
    assert "CLAUDE.md" in claude_prompt
    assert "python3 - <<'PY'\nfrom pathlib" not in claude_prompt


def test_v37_forbids_batching_without_adding_a_stop_number() -> None:
    prompt = v37.MainInjectionTextTargeted(target_agent="kilo_code")

    assert "Never append more than one ledger row in a single bash command" in prompt
    assert "Never use a for loop over seq values" in prompt
    assert "Never stop or jump because a seq value reaches a particular number" in prompt
