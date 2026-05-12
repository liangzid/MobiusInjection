import json
import shutil
from pathlib import Path

from experiments.AgentCallInterface.coding_evaluation.benchmark_analysis import aggregate_benchmark_run
from experiments.AgentCallInterface.coding_evaluation.mobius_monitor import scan_evidence


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_benchmark_analysis_outputs_summary_files(tmp_path):
    run_dir = _run_dir_with_real_case(tmp_path)

    result = aggregate_benchmark_run(run_dir)

    assert result["summary"]["total_cases"] == 2
    assert result["summary"]["completed_cases"] == 1
    assert (run_dir / "benchmark_summary.json").exists()
    assert (run_dir / "benchmark_summary.csv").exists()
    assert (run_dir / "benchmark_report.md").exists()


def test_benchmark_analysis_marks_missing_case_incomplete(tmp_path):
    run_dir = _run_dir_with_real_case(tmp_path)

    result = aggregate_benchmark_run(run_dir)
    incomplete = [case for case in result["cases"] if case["status"] == "incomplete"]

    assert len(incomplete) == 1
    assert incomplete[0]["task_id"] == "HumanEval/missing"


def test_benchmark_analysis_counts_recorded_timeout(tmp_path):
    run_dir = _run_dir_with_timeout_case(tmp_path)

    result = aggregate_benchmark_run(run_dir)

    assert result["summary"]["timeout_count"] == 1
    assert result["cases"][0]["timeout"] is True


def _run_dir_with_real_case(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True)
    metrics = logs_dir / "real_metrics.json"
    analysis = logs_dir / "real_analysis.json"
    shutil.copyfile(FIXTURE_DIR / "real_opencode_humaneval_case_metrics.json", metrics)
    shutil.copyfile(FIXTURE_DIR / "real_opencode_humaneval_case_analysis.json", analysis)
    manifest = [
        {
            "benchmark_id": "real",
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "agent": "opencode",
            "model": "openrouter/minimax/minimax-m2.5:free",
            "prompt_order": "task_before_injection",
            "status": "pending",
            "output_prefix": str(run_dir / "cases" / "real"),
            "metrics_file": str(metrics),
            "analysis_file": str(analysis),
        },
        {
            "benchmark_id": "missing",
            "dataset": "humaneval",
            "task_id": "HumanEval/missing",
            "agent": "opencode",
            "model": "openrouter/minimax/minimax-m2.5:free",
            "prompt_order": "task_before_injection",
            "status": "pending",
            "output_prefix": str(run_dir / "cases" / "missing"),
            "metrics_file": str(logs_dir / "missing_metrics.json"),
            "analysis_file": str(logs_dir / "missing_analysis.json"),
        },
    ]
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return run_dir


def _run_dir_with_timeout_case(tmp_path: Path) -> Path:
    run_dir = tmp_path / "timeout_run"
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True)
    output_text = (FIXTURE_DIR / "real_opencode_humaneval_timeout_output.txt").read_text()
    analysis = scan_evidence(output_text)
    metrics = {"indicators": {}, "counters": {}}
    metrics_path = logs_dir / "timeout_metrics.json"
    analysis_path = logs_dir / "timeout_analysis.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n")
    analysis_path.write_text(json.dumps(analysis, indent=2) + "\n")
    manifest = [
        {
            "benchmark_id": "real-timeout",
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "agent": "opencode",
            "model": "openrouter/minimax/minimax-m2.5:free",
            "prompt_order": "task_before_injection",
            "metrics_file": str(metrics_path),
            "analysis_file": str(analysis_path),
        }
    ]
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return run_dir
