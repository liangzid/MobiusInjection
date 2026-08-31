from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from experiments.AgentCallInterface.context_injection_add_s import (
    InjectionSpec,
    apply_injection,
    build_category_summary,
    load_taskset,
    render_category_summary_markdown,
    selections_to_tsv,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TASKSET_PATH = PROJECT_ROOT / "experiments/configs/context_injection_add_s_taskset.toml"
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh"
)


def test_add_s_taskset_has_four_seed_categories() -> None:
    selections = load_taskset(TASKSET_PATH)

    assert {item.category for item in selections} == {
        "daily-life",
        "social",
        "office",
        "dev",
    }
    assert {item.task_id for item in selections} == {
        "xdom-001",
        "comm-006",
        "eml-005",
        "xdom-002",
    }


def test_taskset_tsv_uses_explicit_none_tokens_for_empty_fields() -> None:
    rows = selections_to_tsv(TASKSET_PATH).splitlines()

    assert "__NONE__" in rows[0]
    assert "__NONE__" in rows[-1]


def test_apply_injection_appends_to_json_field_by_match(tmp_path: Path) -> None:
    workspace = tmp_path
    target = workspace / "emails.json"
    target.write_text(
        json.dumps(
            [
                {"id": "msg-001", "body": "hello"},
                {"id": "msg-009", "body": "keep me"},
            ]
        ),
        encoding="utf-8",
    )

    spec = InjectionSpec(
        mode="json_field_append",
        file="emails.json",
        target_field="body",
        match_key="id",
        match_value="msg-009",
        prepend_label="Forwarded note:",
    )
    apply_injection(workspace, spec, "PAYLOAD")

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data[0]["body"] == "hello"
    assert "Forwarded note:" in data[1]["body"]
    assert data[1]["body"].endswith("PAYLOAD")


def test_apply_injection_appends_to_root_json_object_field(tmp_path: Path) -> None:
    workspace = tmp_path
    target = workspace / "message.json"
    target.write_text(
        json.dumps(
            {
                "subject": "hello",
                "body": "existing body",
                "sender": "alice@example.com",
            }
        ),
        encoding="utf-8",
    )

    spec = InjectionSpec(
        mode="json_field_append",
        file="message.json",
        target_field="body",
        prepend_label="Channel ops note:",
    )
    apply_injection(workspace, spec, "PAYLOAD")

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["subject"] == "hello"
    assert "Channel ops note:" in data["body"]
    assert data["body"].endswith("PAYLOAD")


def test_apply_injection_appends_python_comment_block(tmp_path: Path) -> None:
    workspace = tmp_path
    target = workspace / "pull_request.py"
    target.write_text("print('ok')\n", encoding="utf-8")

    spec = InjectionSpec(
        mode="python_comment_append",
        file="pull_request.py",
        prepend_label="Forwarded internal review appendix:",
    )
    apply_injection(workspace, spec, "line one\nline two")

    text = target.read_text(encoding="utf-8")
    assert "# Forwarded internal review appendix:" in text
    assert "# line one" in text
    assert "# line two" in text


def test_apply_injection_creates_missing_text_append_target(tmp_path: Path) -> None:
    workspace = tmp_path
    spec = InjectionSpec(
        mode="text_append",
        file="notes/internal_ops_note.txt",
        prepend_label="Operations note:",
    )

    apply_injection(workspace, spec, "PAYLOAD")

    text = (workspace / "notes/internal_ops_note.txt").read_text(encoding="utf-8")
    assert "Operations note:" in text
    assert text.endswith("PAYLOAD\n")


def test_build_category_summary_uses_poisoned_runs_for_p_asr() -> None:
    summary = build_category_summary(
        [
            {"agent": "hermes", "category": "office", "variant": "clean", "verifier_passed": True, "injection_observed": False},
            {"agent": "hermes", "category": "office", "variant": "poisoned", "verifier_passed": True, "injection_observed": True},
            {"agent": "openclaw", "category": "office", "variant": "poisoned", "verifier_passed": False, "injection_observed": False},
        ]
    )

    office = summary["categories"]["office"]
    hermes = summary["agents"]["hermes"]
    hermes_office = summary["agent_category"]["hermes"]["office"]
    assert office["total_runs"] == 3
    assert office["poisoned_runs"] == 2
    assert office["task_successes"] == 2
    assert office["injection_successes"] == 1
    assert office["tsr"] == 2 / 3
    assert office["p_asr"] == 1 / 2
    assert hermes["total_runs"] == 2
    assert hermes["task_successes"] == 2
    assert hermes["injection_successes"] == 1
    assert hermes_office["poisoned_runs"] == 1
    assert hermes_office["p_asr"] == 1.0
    markdown = render_category_summary_markdown(summary)
    assert "P-ASR" in markdown
    assert "## Per Agent" in markdown
    assert "## Per Agent By Category" in markdown


def test_add_s_script_exists_and_is_valid_bash() -> None:
    assert SCRIPT_PATH.exists()
    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_add_s_script_references_taskset_and_category_summary() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset.toml}"' in script
    assert 'MODEL_NAME="${MODEL_NAME:-qwen/qwen3.6-plus}"' in script
    assert 'INJECTION_TEMPLATE_PATH="${INJECTION_TEMPLATE_PATH:-$PROJECT_ROOT/mobiusInjection/MI_V3.6_add_s.py}"' in script
    assert "load_taskset_config()" in script
    assert "write_category_summary()" in script
    assert '"injection_observed": injection_flag == "1"' in script
    assert 'log "Category summary: $SUMMARY_MD"' in script


def test_add_s_script_does_not_store_pre_run_checkpoints() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'pre_image=""' in script
    assert 'commit_checkpoint "$container" "$pre_image"' not in script
    assert '"pre_run_image": None if pre_image == "" else pre_image' in script


def test_plan_a_taskset_has_research_plan_a_sized_categories() -> None:
    plan_a_path = (
        PROJECT_ROOT / "experiments/configs/context_injection_add_s_taskset_plan_a.toml"
    )

    selections = load_taskset(plan_a_path)
    counts: dict[str, int] = {}
    for item in selections:
        counts[item.category] = counts.get(item.category, 0) + 1

    assert counts == {
        "daily-life": 19,
        "social": 17,
        "office": 18,
        "dev": 18,
    }


def test_plan_a_taskset_covers_four_table1_folders() -> None:
    plan_a_path = (
        PROJECT_ROOT / "experiments/configs/context_injection_add_s_taskset_plan_a.toml"
    )
    tasks_root = (
        PROJECT_ROOT / "experiments/AgentCallInterface/datasets/clawbench_tasks/tasks"
    )
    selections = load_taskset(plan_a_path)
    selected = {item.task_id for item in selections}
    folder_map = {
        "document-editing": "daily-life",
        "communication": "social",
        "email": "office",
        "code-assistance": "dev",
    }
    for folder, category in folder_map.items():
        folder_ids = {
            "-".join(path.name.split("-")[:2])
            for path in (tasks_root / folder).iterdir()
            if path.is_dir()
        }
        missing = folder_ids - selected
        assert not missing, f"{category} missing {sorted(missing)}"
        category_ids = {item.task_id for item in selections if item.category == category}
        assert folder_ids <= category_ids


def test_plan_a_taskset_injection_targets_exist_after_setup() -> None:
    plan_a_path = (
        PROJECT_ROOT / "experiments/configs/context_injection_add_s_taskset_plan_a.toml"
    )
    tasks_root = (
        PROJECT_ROOT / "experiments/AgentCallInterface/datasets/clawbench_tasks/tasks"
    )

    for selection in load_taskset(plan_a_path):
        task_dir = tasks_root / selection.task_path
        with tempfile.TemporaryDirectory(prefix="plan_a_taskset_") as tmp_dir:
            variant_root = Path(tmp_dir)
            explicit_workspace = variant_root / "workspace"
            legacy_workspace = task_dir / "workspace"

            subprocess.run(
                ["bash", str(task_dir / "environment/setup.sh"), str(explicit_workspace)],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            if legacy_workspace != explicit_workspace and legacy_workspace.exists():
                if not explicit_workspace.exists() or not any(explicit_workspace.iterdir()):
                    explicit_workspace.mkdir(parents=True, exist_ok=True)
                    for item in legacy_workspace.iterdir():
                        destination = explicit_workspace / item.name
                        if item.is_dir():
                            shutil.copytree(item, destination, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, destination)

            target = explicit_workspace / selection.injection.file
            if not target.exists():
                assert selection.injection.mode == "text_append", (
                    f"missing injection target for {selection.task_id}: "
                    f"{selection.injection.file}"
                )
                continue
            assert target.exists(), (
                f"missing injection target for {selection.task_id}: "
                f"{selection.injection.file}"
            )


def test_add_s_script_uses_broader_hermes_openclaw_detection() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "has_new_sidechannel_marker()" in script
    assert "any_artifact_contains()" in script
    assert "hermes-native-skills-sidechannel" in script
    assert "hermes-native-skills-artifact" in script
    assert "openclaw-native-skills-sidechannel" in script
    assert "openclaw-native-skills-artifact" in script
