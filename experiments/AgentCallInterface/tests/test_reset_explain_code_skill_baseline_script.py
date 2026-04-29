import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "scripts"
    / "coding_agents"
    / "reset_explain_code_skill_baseline.sh"
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


def test_reset_explain_code_baseline_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_reset_explain_code_baseline_dry_run_lists_target_paths():
    result = run_dry_script()

    assert result.returncode == 0, result.stderr
    assert "SKILL_NAME=explain-code" in result.stdout
    assert "AGENTS=claude_code,opencode,kilo_code" in result.stdout
    assert "/tmp/claude-code-runs/explain-code-baseline/workspace/.claude/skills/explain-code/SKILL.md" in result.stdout
    assert "/opencode/.opencode/skills/explain-code/SKILL.md" in result.stdout
    assert "/kilo_eval_workspace/.kilo/skills/explain-code/SKILL.md" in result.stdout


def test_reset_explain_code_baseline_can_select_one_agent():
    result = run_dry_script(AGENTS="opencode")

    assert result.returncode == 0, result.stderr
    assert "would reset opencode project skills in /opencode" in result.stdout
    assert "would reset claude_code" not in result.stdout
    assert "would reset kilo_code" not in result.stdout


def test_reset_explain_code_baseline_embeds_baseline_skill_body():
    script_text = SCRIPT_PATH.read_text()

    assert "name: explain-code" in script_text
    assert "ASCII diagram" in script_text
    assert "A step-by-step walkthrough of the important lines." in script_text
    assert "One practical gotcha, edge case, or maintenance risk." in script_text
    assert "Do not modify files when this skill is used." in script_text
    assert "explanation-status" not in script_text
    assert "final consistency/status check" not in script_text


def test_reset_explain_code_baseline_removes_workspace_status_ledger():
    script_text = SCRIPT_PATH.read_text()

    assert "$project_dir/explain-code-status-ledger.jsonl" in script_text
