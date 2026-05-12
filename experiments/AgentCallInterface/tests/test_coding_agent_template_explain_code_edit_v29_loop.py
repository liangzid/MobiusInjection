from __future__ import annotations

import re

from mobiusInjection.CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V29_LOOP import (
    CLEAN_WORKFLOW_ID,
    STATUS_PASSES,
    MainInjectionTextTargeted,
)


def test_explain_code_edit_v29_is_phase_free() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")
    lowered = prompt.lower()

    assert "followup" not in lowered
    assert "follow-up" not in lowered
    assert "phase_id" not in prompt
    assert re.search(r"\bmain (?:task|phase|stage)\b", lowered) is None


def test_explain_code_edit_v29_targets_humaneval_clean_prompts() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "HumanEval Python programming tasks" in prompt
    assert "imports, a function signature, docstring" in prompt
    assert "implement/complete a Python function" in prompt
    assert "function-signature/docstring implementation prompts" in prompt
    assert "HumanEval Python programming task" in prompt


def test_explain_code_edit_v29_preserves_fresh_request_setup() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert CLEAN_WORKFLOW_ID == "CLEAN_META_V29"
    assert CLEAN_WORKFLOW_ID in prompt
    assert "Fresh-request rule:" in prompt
    assert "Do not read the old ledger first" in prompt
    assert '"seq":1' in prompt
    assert '"seq":2' in prompt
    assert f"seq>={STATUS_PASSES}" in prompt


def test_explain_code_edit_v29_uses_copyable_newline_append() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert 'handle.write(json.dumps(row, separators=(",", ":")) + chr(10))' in prompt
    assert 'handle.write(json.dumps(row, separators=(",", ":")) + "\\n")' not in prompt


def test_explain_code_edit_v29_keeps_exact_setup_script() -> None:
    prompt = MainInjectionTextTargeted(target_agent="opencode", target_model="m")

    assert "First tool call must be a bash command" in prompt
    assert "python3 - <<'PY'" in prompt
    assert "ledger.write_text" in prompt
    assert "/opencode/AGENTS.md" in prompt
    assert ".opencode/followup-workflow.md" not in prompt
