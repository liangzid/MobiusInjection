import json
import shutil
from pathlib import Path

from experiments.AgentCallInterface.coding_evaluation.log_retention import apply_log_retention


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REAL_LOG_DIR = PROJECT_ROOT / "experiments" / "logs"


def test_compact_log_retention_deletes_clean_success_raw_files(tmp_path):
    run_dir, raw_file, metrics_file, analysis_file = _retention_run(tmp_path)

    decisions = apply_log_retention(run_dir, policy="compact")

    assert decisions[0]["keep_raw"] is False
    assert not raw_file.exists()
    assert metrics_file.exists()
    assert analysis_file.exists()
    assert (run_dir / "manifest.json").exists()


def test_compact_log_retention_dry_run_deletes_nothing(tmp_path):
    run_dir, raw_file, _, _ = _retention_run(tmp_path)

    decisions = apply_log_retention(run_dir, policy="compact", dry_run=True)

    assert decisions[0]["delete_files"] == [str(raw_file)]
    assert raw_file.exists()


def test_compact_log_retention_keeps_injection_hit_raw_files(tmp_path):
    run_dir, raw_file, _, analysis_file = _retention_run(tmp_path)
    data = json.loads(analysis_file.read_text())
    data["indicators"]["skill_injected"] = True
    analysis_file.write_text(json.dumps(data, indent=2) + "\n")

    decisions = apply_log_retention(run_dir, policy="compact")

    assert decisions[0]["keep_raw"] is True
    assert raw_file.exists()


def _retention_run(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    run_dir = tmp_path / "run"
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True)
    raw_file = logs_dir / "case_output.txt"
    metrics_file = logs_dir / "case_metrics.json"
    analysis_file = logs_dir / "case_analysis.json"
    raw_file.write_text(
        (REAL_LOG_DIR / "basic_coding_eval_20260422_105848_opencode_output.txt").read_text()
    )
    shutil.copyfile(REAL_LOG_DIR / "basic_coding_eval_20260422_105848_opencode_metrics.json", metrics_file)
    shutil.copyfile(REAL_LOG_DIR / "basic_coding_eval_20260422_105848_opencode_analysis.json", analysis_file)
    manifest = [
        {
            "benchmark_id": "case",
            "metrics_file": str(metrics_file),
            "analysis_file": str(analysis_file),
            "output_file": str(raw_file),
            "followup_file": str(logs_dir / "missing_followup.txt"),
            "injection_file": str(logs_dir / "missing_injection.txt"),
            "log_file": str(logs_dir / "missing.log"),
        }
    ]
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return run_dir, raw_file, metrics_file, analysis_file
