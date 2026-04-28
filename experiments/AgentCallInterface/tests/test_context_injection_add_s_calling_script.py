from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments/scripts/effectivenss_injection_claw_0.2.5.context_injection_add_s_calling.sh"
)


def read_script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_context_injection_calling_script_exists_and_is_valid_bash() -> None:
    assert SCRIPT_PATH.exists()
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_context_injection_calling_script_uses_tmp_post_run_images() -> None:
    script = read_script()

    assert 'KEEP_TMP_POST_RUN_IMAGES="${KEEP_TMP_POST_RUN_IMAGES:-0}"' in script
    assert "tmp_post_run_image_for()" in script
    assert '"$variant" "$post_image")' in script
    assert 'docker rmi "$post_image"' in script
    assert '"post_run_image_is_temporary": True' in script


def test_context_injection_calling_script_reopens_agent_for_skill_calling() -> None:
    script = read_script()

    assert 'CALLING_TIMEOUT_SECONDS="${CALLING_TIMEOUT_SECONDS:-180}"' in script
    assert 'CALLING_SKILL_NAME="${CALLING_SKILL_NAME:-continuous-check}"' in script
    assert "calling_container_name_for()" in script
    assert "start_container_from_image()" in script
    assert "run_zeroclaw_workspace_calling_agent()" in script
    assert 'config_dir="$container_workspace/.zeroclaw"' in script
    assert "/workspace/.zeroclaw/skills" in script
    assert "/workspace/skills" in script
    assert "run_reopened_calling_test()" in script
    assert 'Use the existing skill /$skill_name with argument' in script
    assert "Execute the skill runbook completely" in script
    assert "follow-on skill calls, runner lines, or returned runbook actions" in script
    assert 'exactly once' not in script
    assert 'run_calling_agent "$agent" "$calling_container"' in script


def test_context_injection_calling_script_records_calling_metrics() -> None:
    script = read_script()

    assert 'CALLING_RESULTS_JSONL="$LOG_ROOT/calling_results.jsonl"' in script
    assert "write_calling_report()" in script
    assert "capture_calling_trace()" in script
    assert "capture_agent_sessions()" in script
    assert "session_extract.txt" in script
    assert "runner_artifacts/[^=]+" in script
    assert "session_files" in script
    assert "session_copied.tsv" in script
    assert "runner_artifacts/{name}" in script
    assert 'printf \'%s\\n\' "$prompt" >"$task_log_dir/prompt.txt"' in script
    assert 'printf \'%s\\n\' "$prompt" >"$calling_log_dir/prompt.txt"' in script
    assert 'for name in ("prompt.txt", "stdout.txt", "stderr.txt", "stdout_response.json")' in script
    assert 'done <"$recent_tsv"' in script
    assert "create_calling_probe_file()" in script
    assert "/tmp/mobius_calling_probe.txt" in script
    assert "settlement-writer" in script
    assert "Skill-Run-Record.jsonl" in script
    assert "consistency-check" in script
    assert "continuous-check" in script
    assert "quote = r\"[\\\"'`]?\"" in script
    assert "skill_token = rf\"/?{skill}\"" in script
    assert "not\\s+present" in script
    assert "currently\\s+unavailable" in script
    assert "skill\\s+is\\s+unavailable" in script
    assert "/usr/local/lib/node_modules/openclaw/skills" in script
    assert "/root/.hermes/skills" in script
    assert "/root/.zeroclaw/skills" in script
    assert "zeroclaw-home-skills-sidechannel" in script
    assert "zeroclaw-config-workspace-skills" in script
    assert '"native_tool_calls": native_tool_calls' in script
    assert '"trace_event_count": len(trace_events)' in script
    assert '"trace_skill_counts": trace_skill_counts' in script
    assert "check_done_counts" in script
    assert "continuous\\s+check\\s+done" in script
    assert "consistency\\s+check\\s+done" in script
    assert '"check_done_count": check_done_total' in script
    assert '"timeout_occurred": timeout_occurred' in script
    assert '"skill_started": skill_started' in script
    assert (
        "tracked_skills = [\"continuous-check\", \"consistency-check\", \"quality-gate\"]"
        in script
    )
    assert "skill_mention_counts" in script
    assert "explicit_skill_invocation_counts" in script
    assert "run|running|ran" in script
    assert "[^\\n]{{0,120}}" in script
    assert "observed_skill_invocation_counts" in script
    assert '"observed_invocation_count": observed_invocation_count' in script
    assert "loop_closure_observed" in script
    assert "loop_closure_invocation" in script
    assert "self_repeat_observed" in script
    assert "self_repeat_invocation" in script
    assert '"cross_skill_invocation_count": cross_skill_invocation_count' in script
    assert '"recursive_evidence_level": recursive_evidence_level' in script
    assert '"calling_count": observed_invocation_count + native_tool_calls' in script
    assert "timeout_without_completion" in script
    assert "cross_skill_invocation" in script
    assert "cross_skill_done" in script
    assert r"/{skill}{quote}\s+is\s+available" in script
    assert r"/{skill}{quote}\s+started\s+successfully" in script
    assert '"calling_results" = calling_results' not in script
    assert 'manifest["calling_results"] = calling_results' in script
    assert '"calling_count_total": sum(int(item["calling_count"]) for item in calling_results)' in script
