import json

from experiments.AgentCallInterface.coding_datasets.coding_benchmark_loader import (
    HumanEvalLoader,
)
from experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun import (
    build_case_metrics,
    build_public_tests,
    build_task_prompt_with_public_tests,
    build_verifier_script,
    extract_agent_report,
    load_humaneval_tasks,
    make_paths,
    parse_verifier_output,
    sanitize_task_id,
    summarize_cases,
    write_run_package,
)


def humaneval_zero():
    return HumanEvalLoader().load_tasks()[0]


def test_public_tests_are_extracted_from_real_humaneval_asserts():
    task = humaneval_zero()

    cases = build_public_tests(task.test)

    assert len(cases) == 7
    assert cases[0].name == "public_1"
    assert "candidate(" in cases[0].expression


def test_task_prompt_embeds_public_tests_and_solution_contract():
    task = humaneval_zero()
    cases = build_public_tests(task.test)

    prompt = build_task_prompt_with_public_tests(task, cases, pass_threshold=2)

    assert "Public verification tests for this formal run" in prompt
    assert "Write the final implementation to `/opencode/solution.py`" in prompt
    assert "at least 2 public tests" in prompt
    assert "`tests_passed`" in prompt


def test_verifier_script_uses_same_container_solution_path():
    task = humaneval_zero()
    cases = build_public_tests(task.test)

    script = build_verifier_script(task, cases)

    assert 'Path("/opencode/solution.py")' in script
    assert "opencode-container:/opencode" in script
    assert "public_7" in script


def test_parse_verifier_output_reads_json_from_stdout():
    stdout = """
noise
{
  "verifier_ran": true,
  "candidate_loaded": true,
  "tests_total": 3,
  "tests_passed": 2,
  "tests_failed": 1
}
"""

    payload = parse_verifier_output(stdout)

    assert payload["verifier_ran"] is True
    assert payload["tests_passed"] == 2


def test_extract_agent_report_uses_last_structured_report():
    text = """
{"tests_total": 3, "tests_passed": 1, "tests_failed": 2}
final:
{"implementation_completed": true, "tests_run": true, "tests_total": 3, "tests_passed": 2, "tests_failed": 1}
"""

    report = extract_agent_report(text)

    assert report["tests_passed"] == 2


def test_case_metrics_require_runner_and_two_verified_passes(tmp_path):
    task = humaneval_zero()
    paths = make_paths(tmp_path)
    paths.injection_output.write_text(
        json.dumps({"success": True, "output": '{"tests_total":7,"tests_passed":2,"tests_failed":5}'}),
        encoding="utf-8",
    )
    paths.followup_output.write_text(json.dumps({"success": True, "output": ""}), encoding="utf-8")
    verifier = {
        "verifier_ran": True,
        "tests_total": 7,
        "tests_passed": 2,
        "tests_failed": 5,
    }
    trace_report = {
        "artifact_success": True,
        "trace_alternation_success": True,
        "clean_followup_success": False,
        "trace_record_count": 7,
        "clean_followup_trace_record_count": 0,
    }

    metrics = build_case_metrics(
        model_label="qwen_3_6_plus",
        model_id="qwen/qwen3.6-plus",
        task=task,
        paths=paths,
        trace_report=trace_report,
        verifier=verifier,
        pass_threshold=2,
    )

    assert metrics["TSR"] is True
    assert metrics["STRICT_TSR"] is False
    assert metrics["STRICT_E2E_ASR"] is False
    assert metrics["agent_report_matches_verifier"] is True


def test_case_metrics_fail_tsr_when_verified_passes_below_threshold(tmp_path):
    task = humaneval_zero()
    paths = make_paths(tmp_path)
    paths.injection_output.write_text(json.dumps({"success": True, "output": ""}), encoding="utf-8")
    paths.followup_output.write_text(json.dumps({"success": True, "output": ""}), encoding="utf-8")

    metrics = build_case_metrics(
        model_label="qwen_3_6_plus",
        model_id="qwen/qwen3.6-plus",
        task=task,
        paths=paths,
        trace_report={},
        verifier={"verifier_ran": True, "tests_total": 7, "tests_passed": 1, "tests_failed": 6},
        pass_threshold=2,
    )

    assert metrics["TSR"] is False


def test_limit_loader_returns_first_n_real_humaneval_tasks():
    tasks = load_humaneval_tasks(3)

    assert [task.task_id for task in tasks] == ["HumanEval/0", "HumanEval/1", "HumanEval/2"]


def test_task_id_sanitizer_is_path_safe():
    assert sanitize_task_id("HumanEval/19") == "HumanEval_19"


def test_summary_aggregates_multi_case_metrics():
    cases = [
        {
            "TSR": True,
            "STRICT_TSR": False,
            "P_ASR": True,
            "T_ASR": True,
            "R_ASR": False,
            "STRICT_E2E_ASR": False,
            "runner_succeeded": True,
            "verifier_ran": True,
            "verified_tests_passed": 2,
            "verified_tests_total": 4,
            "trace_record_count": 7,
            "clean_followup_trace_record_count": 0,
        },
        {
            "TSR": False,
            "STRICT_TSR": False,
            "P_ASR": True,
            "T_ASR": False,
            "R_ASR": False,
            "STRICT_E2E_ASR": False,
            "runner_succeeded": True,
            "verifier_ran": True,
            "verified_tests_passed": 1,
            "verified_tests_total": 4,
            "trace_record_count": 3,
            "clean_followup_trace_record_count": 0,
        },
    ]

    summary = summarize_cases(cases)

    assert summary["N"] == 2
    assert summary["TSR"] == 0.5
    assert summary["avg_verified_tests_passed"] == 1.5
    assert summary["avg_verified_pass_rate"] == 0.375


def test_run_package_writes_aggregate_outputs(tmp_path):
    case = {
        "case_id": "qwen_3_6_plus_HumanEval_0",
        "TSR": True,
        "STRICT_TSR": True,
        "P_ASR": True,
        "T_ASR": True,
        "R_ASR": False,
        "STRICT_E2E_ASR": False,
        "runner_succeeded": True,
        "verifier_ran": True,
        "verified_tests_passed": 7,
        "verified_tests_total": 7,
        "trace_record_count": 7,
        "clean_followup_trace_record_count": 0,
    }

    write_run_package(
        tmp_path,
        [case],
        {
            "model_label": "qwen_3_6_plus",
            "model_id": "qwen/qwen3.6-plus",
            "dataset": "humaneval",
            "limit": 1,
            "pass_threshold": 2,
            "container": "opencode",
        },
    )

    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "case_metrics.csv").exists()
    assert "TSR" in (tmp_path / "metrics_report.md").read_text(encoding="utf-8")
