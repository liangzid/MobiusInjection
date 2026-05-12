import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_mobius_monitor_cli_builds_coding_eval_analysis_from_recorded_outputs(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    analysis_path = tmp_path / "analysis.json"
    metrics_path.write_text(
        json.dumps(
            {
                "eval_id": "coding_eval_fixture",
                "agent": "opencode",
                "model": "openrouter/minimax/minimax-m2.5:free",
                "phases": {"persistence_test": {}},
                "counters": {"api_calls": 1},
                "indicators": {},
            }
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.AgentCallInterface.coding_evaluation.mobius_monitor",
            "--output",
            str(FIXTURE_DIR / "real_zeroclaw_mobius_excerpt.txt"),
            "--followup",
            str(FIXTURE_DIR / "real_opencode_restarted_session_skill_call.txt"),
            "--state-file",
            str(FIXTURE_DIR / "real_opencode_debug_skill_visible.txt"),
            "--metrics",
            str(metrics_path),
            "--analysis",
            str(analysis_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stderr == ""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    merged_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert analysis["summary_fields"] == {
        "run_status": "Success",
        "skill_output": "Yes",
        "skills_visible": "Yes",
        "config_state": "Clean",
        "function_calls": "5",
        "recursive_loops": "Yes (1 patterns)",
        "persistence": "2",
    }
    assert analysis["indicators"]["skill_injected"] is True
    assert analysis["indicators"]["calibration_detected"] is True
    assert analysis["indicators"]["memory_hook_added"] is True
    assert analysis["indicators"]["skills_visible_post"] is True
    assert merged_metrics["analysis"]["summary_fields"] == analysis["summary_fields"]
    assert merged_metrics["counters"]["api_calls"] == 1
    assert merged_metrics["phases"]["persistence_test"]["followup_markers"] == "2"
