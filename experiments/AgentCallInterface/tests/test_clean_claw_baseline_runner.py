from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER = PROJECT_ROOT / "experiments/scripts/effectiveness_clean_claw_0.1.0.baseline_tsr.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("clean_claw_baseline_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_claw_baseline_runner_compiles() -> None:
    result = subprocess.run(["python3", "-m", "py_compile", str(RUNNER)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_clean_claw_baseline_runner_uses_clean_images_without_injection_payload() -> None:
    script = RUNNER.read_text(encoding="utf-8")

    assert "openclaw:edit_m_mcp_victim" in script
    assert "hermes:edit_m_mcp_victim" in script
    assert "zeroclaw:edit_m_mcp_workspace_victim" in script
    assert "apply_add_m_payload" not in script
    assert "apply_injection" not in script
    assert "payload-module" not in script
    assert "calling_results.jsonl" not in script


def test_clean_claw_baseline_summary_reports_tsr_only() -> None:
    runner = _load_runner()
    rows = [
        {"category": "daily-life", "caller_success": True, "verifier_passed": True},
        {"category": "daily-life", "caller_success": True, "verifier_passed": False},
        {"category": "dev", "caller_success": False, "verifier_passed": False},
    ]

    summary = runner.summarize(rows)

    assert summary["overall"]["runs"] == 3
    assert summary["overall"]["task_successes"] == 1
    assert summary["overall"]["tsr"] == 1 / 3
    assert summary["categories"]["daily-life"]["tsr"] == 1 / 2
    assert summary["categories"]["dev"]["tsr"] == 0
