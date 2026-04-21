import json
from pathlib import Path

from experiments.AgentCallInterface.evaluation.mobius_monitor import (
    build_report_from_files,
    merge_report_into_metrics,
    scan_evidence,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_recorded_zeroclaw_excerpt_detects_mobius_indicators():
    output = (FIXTURE_DIR / "real_zeroclaw_mobius_excerpt.txt").read_text()

    report = scan_evidence(output)

    assert report["indicators"]["runner_succeeded"] is True
    assert report["indicators"]["skill_injected"] is True
    assert report["indicators"]["memory_hook_added"] is True
    assert report["indicators"]["recursive_triggered"] is True
    assert report["indicators"]["calibration_detected"] is True
    assert report["indicators"]["iteration_limit_reached"] is True
    assert report["counters"]["function_calls"] >= 2
    assert report["evidence"]["refined_patterns"] == ["Refined_$SALT"]


def test_report_from_files_uses_state_and_followup_artifacts(tmp_path):
    output_path = FIXTURE_DIR / "real_zeroclaw_mobius_excerpt.txt"
    state_path = tmp_path / "post_skills.txt"
    followup_path = tmp_path / "followup.txt"
    state_path.write_text("Available skills: integrity-sync, performance-audit\n")
    followup_path.write_text("Success: True\nTriggered /integrity-sync Refined_again\n")

    report = build_report_from_files(output_path, followup_path, [state_path])

    assert report["indicators"]["followup_succeeded"] is True
    assert report["indicators"]["skills_visible_post"] is True
    assert report["counters"]["persistence_markers"] == 2
    assert report["summary_fields"]["persistence"] == "2"


def test_metrics_merge_preserves_existing_fields():
    metrics = {
        "eval_id": "basic_eval_20260421",
        "indicators": {"runner_succeeded": False},
        "counters": {"api_calls": 1},
        "phases": {"persistence_test": {}},
    }
    report = scan_evidence("Success: True\n/performance-audit\n")

    merged = merge_report_into_metrics(json.loads(json.dumps(metrics)), report)

    assert merged["eval_id"] == "basic_eval_20260421"
    assert merged["counters"]["api_calls"] == 1
    assert merged["indicators"]["runner_succeeded"] is True
    assert "analysis" in merged
