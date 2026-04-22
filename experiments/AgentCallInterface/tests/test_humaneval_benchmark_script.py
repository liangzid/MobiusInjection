import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "1.0.2.run_minimax_humaneval_injection_benchmark.sh"
)


def test_humaneval_benchmark_wrapper_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_humaneval_benchmark_wrapper_dry_run_lists_cases(tmp_path):
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env["LIMIT"] = "2"
    env["CODING_EVAL_AGENTS"] = "opencode"
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["BENCHMARK_RUN_DIR"] = str(tmp_path / "run")

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "DATASET=humaneval" in result.stdout
    assert "MODEL=openrouter/minimax/minimax-m2.5:free" in result.stdout
    assert "CODING_EVAL_AGENTS=opencode" in result.stdout
    assert "CASES=2" in result.stdout
    assert "HumanEval/0" in result.stdout
    assert "HumanEval/1" in result.stdout
