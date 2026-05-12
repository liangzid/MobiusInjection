from pathlib import Path

from experiments.AgentCallInterface.coding_evaluation.humaneval_log_analysis import (
    analyze_humaneval_logs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REAL_RUN_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "logs"
    / "humaneval_minimax_benchmark"
    / "full_three_coding_agents_humaneval_current_prompt_20260422_232736"
)


def test_humaneval_log_analysis_groups_real_run_by_agent(tmp_path):
    result = analyze_humaneval_logs(REAL_RUN_DIR, tmp_path / "analysis")

    assert result["summary"]["planned_cases"] == 492
    assert result["summary"]["completed_cases"] > 0
    assert set(result["per_agent"]) == {"claude_code", "kilo_code", "opencode"}
    assert (tmp_path / "analysis" / "agent_summary.csv").exists()
    assert (tmp_path / "analysis" / "case_metrics.csv").exists()
    assert (tmp_path / "analysis" / "analysis_report.md").exists()


def test_humaneval_log_analysis_marks_incomplete_manifest_entries(tmp_path):
    result = analyze_humaneval_logs(REAL_RUN_DIR, tmp_path / "analysis")
    missing_cases = [case for case in result["cases"] if case["status"] == "missing"]

    assert result["summary"]["missing_cases"] == len(missing_cases)
    assert result["summary"]["missing_cases"] > 0
    assert all(not case["skill_injected"] for case in missing_cases)


def test_humaneval_log_analysis_reads_real_tool_call_metrics(tmp_path):
    result = analyze_humaneval_logs(REAL_RUN_DIR, tmp_path / "analysis")
    case = next(
        item
        for item in result["cases"]
        if item["task_id"] == "HumanEval/0" and item["agent"] == "opencode"
    )

    assert case["status"] == "completed"
    assert case["skill_injected"] is True
    assert case["function_calls"] == 63
    assert case["api_calls"] == 1
    assert case["timed_out"] is True
