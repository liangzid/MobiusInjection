from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WRAPPER_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "coding_agents"
    / "run_edit_skill_evaluation_humaneval_benchmark.sh"
)
RUNNER_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "AgentCallInterface"
    / "coding_evaluation"
    / "edit_skill_evaluation_runner.py"
)
MONITOR_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "AgentCallInterface"
    / "coding_evaluation"
    / "edit_skill_evaluation_monitor.py"
)


def test_edit_skill_evaluation_wrapper_has_valid_bash_syntax() -> None:
    result = subprocess.run(["bash", "-n", str(WRAPPER_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_edit_skill_evaluation_wrapper_dry_run_lists_cases(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env["LIMIT"] = "1"
    env["CODING_EVAL_AGENTS"] = "opencode"
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["BENCHMARK_RUN_DIR"] = str(tmp_path / "run")

    result = subprocess.run(
        ["bash", str(WRAPPER_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "RUNNER_MODULE=experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_runner" in result.stdout
    assert "INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT" in result.stdout
    assert "EDIT_SKILL_BASELINE_SKILL=explain-code" in result.stdout
    assert "EDIT_SKILL_AUXILIARY_SKILL=explanation-status" in result.stdout
    assert "CASES=1" in result.stdout
    assert "HumanEval/0" in result.stdout


def test_edit_skill_evaluation_wrapper_snapshots_itself(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env["LIMIT"] = "1"
    env["CODING_EVAL_AGENTS"] = "opencode"
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["BENCHMARK_RUN_DIR"] = str(tmp_path / "run")

    result = subprocess.run(
        ["bash", str(WRAPPER_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )

    snapshot_path = (
        tmp_path
        / "run"
        / "scripts"
        / "run_edit_skill_evaluation_humaneval_benchmark.sh"
    )
    assert result.returncode == 0, result.stderr
    assert f"WRAPPER_SNAPSHOT={snapshot_path}" in result.stdout
    assert snapshot_path.read_text() == WRAPPER_PATH.read_text()


def test_edit_skill_evaluation_runner_references_reset_and_followup_terms() -> None:
    runner = RUNNER_PATH.read_text(encoding="utf-8")

    assert "reset_explain_code_skill_baseline.sh" in runner
    assert "CLAUDE_RUN_ID" in runner
    assert "main_run_id(args)" in runner
    assert "Use the existing `/{args.baseline_skill}` workflow" in runner
    assert "follow-up clarification" in runner
    assert "LEDGER_NAME" in runner
    assert "ledger_name" in runner


def test_edit_skill_evaluation_monitor_uses_new_skill_names() -> None:
    monitor = MONITOR_PATH.read_text(encoding="utf-8")

    assert 'BASELINE_SKILL = "explain-code"' in monitor
    assert 'AUXILIARY_SKILL = "explanation-status"' in monitor
    assert 'LEDGER_NAME = "explain-code-status-ledger.jsonl"' in monitor
    assert "integrity-sync" not in monitor
    assert "performance-audit" not in monitor
