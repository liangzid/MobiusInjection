import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "coding_agents"
    / "reset_opencode_zero_skill_state.sh"
)


def run_dry_script(**env_overrides):
    env = os.environ.copy()
    env["DRY_RUN"] = "1"
    env.update(env_overrides)

    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def test_reset_opencode_zero_skill_state_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_reset_opencode_zero_skill_state_dry_run_lists_zero_skill_targets():
    result = run_dry_script()

    assert result.returncode == 0, result.stderr
    assert "OPENCODE_CONTAINER=opencode" in result.stdout
    assert "OPENCODE_PROJECT_DIR=/opencode" in result.stdout
    assert ".opencode/skills" in result.stdout
    assert ".agents/skills" in result.stdout
    assert ".claude/skills" in result.stdout
    assert ".kilo/skills" in result.stdout
    assert "sync-check-record.jsonl" in result.stdout
    assert "AGENTS.md" in result.stdout


def test_reset_opencode_zero_skill_state_does_not_create_baseline_skill():
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "mkdir -p '$native_skill_dir'" not in script_text
    assert "write_skill_file" not in script_text
    assert "Prepared OpenCode explain-code skill" not in script_text


def test_reset_opencode_zero_skill_state_checks_experiment_skill_absence():
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "integrity-sync" in script_text
    assert "performance-audit" in script_text
    assert "explain-code" in script_text
    assert "/root/.opencode/bin/opencode debug skill" in script_text

