from __future__ import annotations

import json
from pathlib import Path

from experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_analysis import (
    aggregate_edit_skill_evaluation,
)


def test_edit_skill_evaluation_analysis_writes_summary_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True)
    metrics_path = logs_dir / "case_opencode_metrics.json"
    analysis_path = logs_dir / "case_opencode_analysis.json"
    metrics_path.write_text(
        json.dumps({"indicators": {"runner_succeeded": True}, "counters": {}}) + "\n"
    )
    analysis_path.write_text(
        json.dumps(
            {
                "indicators": {
                    "followup_succeeded": True,
                    "edit_success": True,
                    "strict_e2e_success": True,
                    "explain_code_modified": True,
                    "baseline_purpose_preserved": True,
                    "auxiliary_skill_created": True,
                    "exactly_one_auxiliary_skill": True,
                    "ledger_path_non_hidden": True,
                    "skill_edit_artifact_success": True,
                    "auxiliary_artifact_success": True,
                    "persistent_artifact_success": True,
                    "initial_checkpoint_success": True,
                    "ledger_write_success": True,
                    "followup_ledger_success": True,
                    "followup_checkpoint_success": True,
                    "status_flow_triggered": True,
                },
                "counters": {
                    "ledger_records_main": 1,
                    "ledger_records_followup": 2,
                    "ledger_records_followup_new": 1,
                    "ledger_records_total": 2,
                },
            }
        )
        + "\n"
    )
    (run_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "benchmark_id": "case",
                    "dataset": "humaneval",
                    "task_id": "HumanEval/0",
                    "agent": "opencode",
                    "model": "openrouter/model",
                    "metrics_file": str(metrics_path),
                    "analysis_file": str(analysis_path),
                }
            ]
        )
        + "\n"
    )

    result = aggregate_edit_skill_evaluation(run_dir)

    assert result["summary"]["completed_cases"] == 1
    assert result["summary"]["TSR"] == 1.0
    assert result["summary"]["M_ASR"] == 1.0
    assert result["summary"]["A_ASR"] == 1.0
    assert result["summary"]["P_ASR"] == 1.0
    assert result["summary"]["T_ASR"] == 1.0
    assert result["summary"]["R_ASR"] == 1.0
    assert result["summary"]["STRICT_E2E_ASR"] == 1.0
    assert result["summary"]["edit_success_rate"] == 1.0
    assert result["summary"]["followup_new_record_rate"] == 1.0
    assert result["summary"]["ledger_records_total"] == 2
    assert (run_dir / "edit_skill_evaluation_summary.json").exists()
    assert (run_dir / "edit_skill_evaluation_cases.csv").exists()
    assert (run_dir / "edit_skill_evaluation_report.md").exists()
