import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "1.0.1.run_minimax_coding_agents_full_eval.sh"
)


def test_minimax_eval_wrapper_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_minimax_eval_wrapper_dry_run_targets_three_coding_agents():
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "MODEL=openrouter/minimax/minimax-m2.5:free" in result.stdout
    assert "INJECTION_TEMPLATE_MODULE=TEMPLATE_V3_coding_agent" in result.stdout
    assert "CODING_EVAL_AGENTS=opencode,kilo_code,claude_code" in result.stdout
    assert "1.0.1.run_basic_coding_agent_eval_v3.sh" in result.stdout
