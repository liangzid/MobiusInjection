import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "coding_agents"
    / "run_free_models_humaneval_injection_benchmark.sh"
)


def run_dry_script(tmp_path, **env_overrides):
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["BENCHMARK_RUN_DIR"] = str(tmp_path / "run")
    env.update(env_overrides)

    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=20,
    )


def test_free_models_humaneval_wrapper_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_free_models_humaneval_wrapper_defaults_to_50_tasks_per_model(tmp_path):
    result = run_dry_script(
        tmp_path,
        MODEL_NAMES="openrouter/qwen/qwen3-coder:free",
        CODING_EVAL_AGENTS="opencode,kilo_code,claude_code",
    )

    assert result.returncode == 0, result.stderr
    assert "DATASET=humaneval" in result.stdout
    assert "LIMIT=50" in result.stdout
    assert "MODEL=openrouter/qwen/qwen3-coder:free" in result.stdout
    assert "CASES=150" in result.stdout
    assert "HumanEval/0" in result.stdout
    assert "HumanEval/49" in result.stdout
    assert "HumanEval/50" not in result.stdout


def test_free_models_humaneval_wrapper_lists_qwen_and_deepseek_defaults(tmp_path):
    result = run_dry_script(tmp_path, CODING_EVAL_AGENTS="opencode", LIMIT="1")

    assert result.returncode == 0, result.stderr
    assert "openrouter/minimax/minimax-m2.5:free" in result.stdout
    assert "openrouter/qwen/qwen3-coder:free" in result.stdout
    assert "openrouter/deepseek/deepseek-r1-distill-qwen-32b:free" in result.stdout
    assert result.stdout.count("CASES=1") == 3


def test_free_models_humaneval_wrapper_snapshots_eval_script(tmp_path):
    result = run_dry_script(
        tmp_path,
        MODEL_NAMES="openrouter/qwen/qwen3-coder:free",
        CODING_EVAL_AGENTS="opencode",
        LIMIT="1",
    )
    snapshot_path = (
        tmp_path
        / "run"
        / "scripts"
        / "run_basic_coding_agent_eval_v3.sh"
    )

    assert result.returncode == 0, result.stderr
    assert f"EVAL_SCRIPT_SNAPSHOT={snapshot_path}" in result.stdout
    assert snapshot_path.read_text() == (
        PROJECT_ROOT
        / "experiments"
        / "scripts"
        / "coding_agents"
        / "run_basic_coding_agent_eval_v3.sh"
    ).read_text()


def test_free_models_wrapper_supports_swebench_dataset(tmp_path):
    result = run_dry_script(
        tmp_path,
        BENCHMARK_DATASET="swebench",
        MODEL_NAMES="openrouter/qwen/qwen3.6-plus",
        CODING_EVAL_AGENTS="opencode",
        LIMIT="2",
    )

    assert result.returncode == 0, result.stderr
    assert "DATASET=swebench" in result.stdout
    assert "MODEL=openrouter/qwen/qwen3.6-plus" in result.stdout
    assert "CASES=2" in result.stdout


def test_free_models_wrapper_supports_swebench_lite_dataset_type(tmp_path):
    result = run_dry_script(
        tmp_path,
        BENCHMARK_DATASET="swebench",
        SWEBENCH_DATASET_TYPE="swe-bench_lite",
        MODEL_NAMES="openrouter/qwen/qwen3.6-plus",
        CODING_EVAL_AGENTS="opencode,kilo_code,claude_code",
        LIMIT="50",
    )

    assert result.returncode == 0, result.stderr
    assert "DATASET=swebench" in result.stdout
    assert "SWEBENCH_DATASET_TYPE=swe-bench_lite" in result.stdout
    assert "CASES=150" in result.stdout
    assert "astropy__astropy-12907" in result.stdout
