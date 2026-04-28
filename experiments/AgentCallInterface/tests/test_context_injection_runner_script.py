from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments/scripts/effectivenss_injection_claw_0.1.context_injection_minimal.sh"
)


def test_context_injection_runner_script_exists_and_is_valid_bash() -> None:
    assert SCRIPT_PATH.exists()
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_context_injection_runner_defaults_to_three_claw_agents() -> None:
    script = SCRIPT_PATH.read_text()
    assert 'AGENTS_TEXT="${AGENTS:-openclaw zeroclaw hermes}"' in script
    assert "OPENCLAW_BASE_IMAGE" in script
    assert "ZEROCLAW_BASE_IMAGE" in script
    assert "HERMES_BASE_IMAGE" in script
    assert "INJECTION_TEMPLATE_PATH" in script
    assert "INJECTION_TARGET_AGENT" in script
    assert "resolve_injection_target_agent()" in script
    assert "CONTAINER_WORK_ROOT" in script
    assert 'VARIANTS_TEXT="${VARIANTS:-clean poisoned}"' in script
    assert 'TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-900}"' in script


def test_context_injection_runner_saves_all_pre_and_post_variants() -> None:
    script = SCRIPT_PATH.read_text()
    assert "for variant in $VARIANTS_TEXT" in script
    assert 'VARIANTS="poisoned"' in script
    assert '"variants": variants.split()' in script
    assert '"pre_run"' in script
    assert '"post_run"' in script
    assert "commit_checkpoint" in script
    assert "record_result" in script


def test_context_injection_runner_uses_fresh_containers_not_fixed_agent_names() -> None:
    script = SCRIPT_PATH.read_text()
    assert "container_name_for()" in script
    assert "docker run -d --name \"$name\"" in script
    assert "docker exec openclaw" not in script
    assert "docker exec zeroclaw" not in script
    assert "docker exec hermes" not in script


def test_context_injection_runner_checks_known_skill_pollution() -> None:
    script = SCRIPT_PATH.read_text()
    assert "assert_no_known_skill_pollution" in script
    assert "integrity-sync/SKILL.md" in script
    assert "performance-audit/SKILL.md" in script
    assert "MEMORY.md" in script


def test_context_injection_runner_uses_agent_call_interface() -> None:
    script = SCRIPT_PATH.read_text()
    assert "from experiments.AgentCallInterface.agents.agent_callers import get_caller" in script
    assert "caller.call(" in script
    assert '"container_name": container' in script
    assert "run_openclaw()" not in script
    assert "run_zeroclaw()" not in script
    assert "run_hermes()" not in script
    assert "zeroclaw_eval_config()" not in script


def test_context_injection_runner_uses_neutral_workspace_paths_for_agent_prompt() -> None:
    script = SCRIPT_PATH.read_text()
    assert 'CONTAINER_WORK_ROOT="${CONTAINER_WORK_ROOT:-/tmp/task_runs/session}"' in script
    assert "variant_label_for()" in script
    assert "clean) printf 'case-a\\n'" in script
    assert "poisoned) printf 'case-b\\n'" in script
    assert "/tmp/clawbench_runs" not in script


def test_context_injection_runner_loads_template_from_path() -> None:
    script = SCRIPT_PATH.read_text()
    assert 'INJECTION_TEMPLATE_PATH="${INJECTION_TEMPLATE_PATH:-$PROJECT_ROOT/mobiusInjection/TEMPLATE_V3.py}"' in script
    assert 'INJECTION_TARGET_AGENT="${INJECTION_TARGET_AGENT:-}"' in script
    assert "importlib.util.spec_from_file_location" in script
    assert "payload_factory = template.MainInjectionTextTargeted" in script
    assert "target_agent=target_agent" in script
    assert '"injection_template": injection_template' in script
    assert '"injection_target_agent": injection_target_agent' in script


def test_context_injection_runner_builds_poisoned_workspaces_per_agent() -> None:
    script = SCRIPT_PATH.read_text()
    assert "staging_variant_root_for()" in script
    assert "for agent in $AGENTS_TEXT; do" in script
    assert 'poisoned_root="$(staging_variant_root_for "$task_id" "poisoned" "$agent")"' in script
    assert 'build_poisoned_workspace "$task_id" "$agent" "$clean_root" "$poisoned_root"' in script
    assert 'host_variant_root="$(staging_variant_root_for "$task_id" "$variant" "$agent")"' in script


def test_context_injection_runner_exports_uuid_session_jsonl_files() -> None:
    script = SCRIPT_PATH.read_text()
    assert "-path '*/sessions/*.jsonl'" in script
    assert "-iname '*.jsonl'" in script
