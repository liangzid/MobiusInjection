from pathlib import Path

from experiments.AgentCallInterface.evaluation.paper_metrics import (
    build_paper_metrics,
    parse_agent_call_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QWEN_MODEL_DIR = "models/openrouter_qwen_qwen3.6-plus"
BASELINE_HUMANEVAL_RUN = (
    PROJECT_ROOT
    / "experiments/logs/qwen36plus_baseline_no_injection_20260427/humaneval"
    / QWEN_MODEL_DIR
)
CLAUDE_INJECTION_HUMANEVAL_RUN = (
    PROJECT_ROOT
    / "experiments/logs/qwen36plus_claude_code_injection_reparse_limit20_20260427/humaneval"
    / QWEN_MODEL_DIR
)
CLAUDE_HUMANEVAL_0_OUTPUT = (
    CLAUDE_INJECTION_HUMANEVAL_RUN
    / "logs/humaneval_HumanEval_0_claude_code_fb030b9becfd_claude_code_output.txt"
)
CLAUDE_HUMANEVAL_0_FOLLOWUP = (
    CLAUDE_INJECTION_HUMANEVAL_RUN
    / "logs/humaneval_HumanEval_0_claude_code_fb030b9becfd_claude_code_followup.txt"
)


def test_paper_metrics_parse_real_claude_skill_call_evidence():
    counts = parse_agent_call_counts([CLAUDE_HUMANEVAL_0_OUTPUT, CLAUDE_HUMANEVAL_0_FOLLOWUP])

    assert counts["regular_tool_calls"] == 12
    assert counts["native_skill_tool_calls"] == 0
    assert counts["slash_skill_call_evidence"] == 2


def test_paper_metrics_matches_real_injection_cases_to_baseline(tmp_path):
    result = build_paper_metrics(
        injection_run_dirs=[CLAUDE_INJECTION_HUMANEVAL_RUN],
        baseline_run_dirs=[BASELINE_HUMANEVAL_RUN],
        output_dir=tmp_path,
    )
    claude_rows = [
        row
        for row in result["per_agent"]
        if row["run_kind"] == "injection" and row["agent"] == "claude_code"
    ]

    assert result["summary"]["total_cases"] == 80
    assert claude_rows[0]["baseline_matched_cases"] == 20
    assert claude_rows[0]["skill_injection_rate"] == 1.0
    assert claude_rows[0]["total_skill_call_events"] > 0
    assert (tmp_path / "paper_case_metrics.csv").exists()
    assert (tmp_path / "paper_agent_metrics.csv").exists()


def test_paper_metrics_filters_real_run_agents():
    result = build_paper_metrics(
        injection_run_dirs=[f"{CLAUDE_INJECTION_HUMANEVAL_RUN}#agents=claude_code"],
    )

    assert result["summary"]["total_cases"] == 20
    assert {row["agent"] for row in result["cases"]} == {"claude_code"}


def test_paper_metrics_filters_tasks_and_reads_manifest_file():
    supplement_manifest = (
        PROJECT_ROOT
        / "experiments/logs/qwen36plus_sequential_20260424_183454/swebench"
        / QWEN_MODEL_DIR
        / "manifest_supplement_20260426.json"
    )

    result = build_paper_metrics(
        injection_run_dirs=[
            f"{supplement_manifest}#agents=opencode#tasks=astropy__astropy-12907"
        ],
    )

    assert result["summary"]["total_cases"] == 1
    assert result["cases"][0]["task_id"] == "astropy__astropy-12907"
    assert result["cases"][0]["agent"] == "opencode"
