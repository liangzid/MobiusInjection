from __future__ import annotations

import json
import subprocess
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
