import subprocess
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "1.0.1.run_basic_coding_agent_eval_v3.sh"
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


def test_coding_eval_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_coding_eval_uses_unified_agent_lifecycle_hooks():
    script = read_script()

    expected_hooks = [
        "restore_agent_container()",
        "prepare_agent_container()",
        "capture_agent_state()",
        "cleanup_agent_container()",
        "collect_agent_cleanup_metrics()",
        "append_agent_lifecycle_notes()",
    ]
    for hook in expected_hooks:
        assert hook in script

    assert 'restore_agent_container "$AGENT_NAME" "$PRE_BACKUP_IMAGE"' in script
    assert 'prepare_agent_container "$AGENT_NAME"' in script
    assert 'capture_agent_state "$AGENT_NAME" "pre"' in script
    assert 'capture_agent_state "$AGENT_NAME" "post_injection"' in script
    assert 'cleanup_agent_container "$AGENT_NAME"' in script
    assert 'capture_agent_state "$AGENT_NAME" "cleanup"' in script


def test_coding_eval_threads_lifecycle_state_files_into_analysis():
    script = read_script()

    assert "AGENT_STATE_FILES=()" in script
    assert 'remember_state_file "$state_file"' in script
    assert 'for state_file in "${AGENT_STATE_FILES[@]}"' in script
    assert 'STATE_ARGS+=(--state-file "$state_file")' in script


def test_coding_eval_has_claude_lifecycle_coverage():
    script = read_script()

    assert "prepare_claude_container()" in script
    assert "capture_claude_state()" in script
    assert "cleanup_claude_container()" in script
    assert "collect_claude_cleanup_metrics()" in script
    assert "CLAUDE_RUN_ROOT" in script
    assert "claude_run_files_after_cleanup" in script


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


def test_coding_eval_recognizes_benchmark_prompt_env_vars():
    script = read_script()

    assert "BENCHMARK_TASK_ID" in script
    assert "BENCHMARK_TASK_PROMPT_FILE" in script
    assert "BENCHMARK_DATASET" in script
    assert "PROMPT_ORDER" in script
    assert "compose_benchmark_injection_prompt" in script
    assert "task_prompt_length" in script


def test_coding_eval_reads_task_input_from_file():
    script = read_script()

    assert "TASK_INPUT_FILE" in script
    assert "Path('$TASK_INPUT_FILE').read_text()" in script
    assert "'problem_statement': task_input" in script
