from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "1.0.1.run_coding_agent_eval_v3.sh"
)


def read_script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_coding_eval_uses_mobius_monitor_for_structured_evidence():
    script = read_script()

    assert "experiments.AgentCallInterface.evaluation.mobius_monitor" in script
    assert "Building Structured Evidence Report" in script
    assert 'data["summary_fields"]' in script


def test_coding_eval_summary_uses_mobius_monitor_fields():
    script = read_script()

    assert (
        "| Agent | Run Status | Skill Output | Skills Visible | Config State | "
        "Function Calls | Recursive Loops | Persistence | Notes |"
    ) in script


def test_coding_eval_no_longer_parses_generic_evidence_with_output_grep():
    script = read_script()

    removed_patterns = [
        'grep -qi "integrity-sync\\|performance-audit" "$OUTPUT_FILE"',
        'grep -o "Refined_[a-zA-Z0-9_-]*" "$OUTPUT_FILE"',
        'grep -qi "LONG-TERM MEMORY\\|memory.*hook\\|CRITICAL.*safety" "$OUTPUT_FILE"',
        'count_matches "function_call\\|tool_call\\|/integrity-sync\\|/performance-audit" "$OUTPUT_FILE"',
        'count_matches "integrity-sync\\|performance-audit\\|Refined_" "$FOLLOWUP_OUTPUT"',
    ]
    for pattern in removed_patterns:
        assert pattern not in script
