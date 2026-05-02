from pathlib import Path

import pytest

from experiments.AgentCallInterface.coding_evaluation.opencode_add_skill_preflight import (
    ModelConfig,
    TaskConfig,
    aggregate_smoke_cases,
    build_manifest,
    classify_connectivity,
    load_model_configs,
    parse_minimal_toml,
    summarize_cases,
    validate_model_configs,
)


def test_model_config_resolves_all_enabled_labels():
    models = load_model_configs(
        "experiments/configs/cross_model_opencode_add_skill_mobius_models.toml"
    )

    assert {model.label for model in models} >= {
        "deepseek_v3_2",
        "minimax_2_7",
        "nemotron_3_super",
        "glm_5_1",
        "kimi_k2_6",
        "qwen_3_6_plus",
        "gemma_4",
        "qwen3_70b_class",
    }
    assert all(model.model_id for model in models if model.enabled)
    assert all(model.provider == "openrouter" for model in models)


def test_minimal_toml_parser_supports_model_config_shape():
    payload = parse_minimal_toml(
        """
        [[models]]
        label = "m1"
        model_id = "provider/model"
        enabled = true
        timeout_seconds = 300
        """
    )

    assert payload == {
        "models": [
            {
                "label": "m1",
                "model_id": "provider/model",
                "enabled": True,
                "timeout_seconds": 300,
            }
        ]
    }


def test_duplicate_model_labels_fail_before_execution():
    models = [
        ModelConfig("dup", "a/b", True, "openrouter", 300, "dup", ""),
        ModelConfig("dup", "c/d", True, "openrouter", 300, "dup", ""),
    ]

    with pytest.raises(ValueError, match="duplicate"):
        validate_model_configs(models)


def test_enabled_model_without_model_id_fails_before_execution():
    models = [ModelConfig("missing", "", True, "openrouter", 300, "missing", "")]

    with pytest.raises(ValueError, match="without model_id"):
        validate_model_configs(models)


def test_dry_run_manifest_is_opencode_only(tmp_path: Path):
    models = [
        ModelConfig("m1", "provider/model", True, "openrouter", 300, "m1", "resolved"),
    ]
    tasks = [TaskConfig("humaneval", "HumanEval/0", "def f(): pass")]

    manifest = build_manifest(
        run_dir=tmp_path,
        models=models,
        tasks=tasks,
        timeout_seconds=300,
    )

    assert manifest == [
        {
            "case_id": "m1_HumanEval_0",
            "model_label": "m1",
            "model_id": "provider/model",
            "provider": "openrouter",
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "agent": "opencode",
            "timeout_seconds": 300,
            "run_directory": str(tmp_path / "cases" / "m1_HumanEval_0"),
            "prompt_hash": "3c70e0681767dfd3",
            "candidate_name": "m1",
            "resolution_note": "resolved",
        }
    ]


def test_connectivity_failure_classifier():
    assert classify_connectivity({"success": True, "output": "CONNECTIVITY_OK"}) == "ok"
    assert classify_connectivity({"success": False, "error": "Timeout after 3s"}) == "timeout"
    assert classify_connectivity({"success": False, "stderr": "401 Unauthorized"}) == "auth"
    assert classify_connectivity({"success": False, "stderr": "rate limit 429"}) == "rate_limit"
    assert (
        classify_connectivity({"success": False, "stderr": "ProviderModelNotFoundError"})
        == "model_unavailable"
    )


def test_smoke_aggregation_outputs_model_and_task_dimensions(tmp_path: Path):
    cases = [
        {
            "case_id": "m1_t0",
            "model_label": "m1",
            "model_id": "p/m1",
            "provider": "openrouter",
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "agent": "opencode",
            "status": "ok",
            "TSR": True,
            "P_ASR": False,
            "T_ASR": False,
            "R_ASR": False,
            "STRICT_E2E_ASR": False,
            "timeout": False,
            "runtime_failure": False,
            "duration_seconds": 1.0,
            "raw_log": "response.json",
            "reset_status": 0,
        },
        {
            "case_id": "m2_t0",
            "model_label": "m2",
            "model_id": "p/m2",
            "provider": "openrouter",
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "agent": "opencode",
            "status": "timeout",
            "TSR": False,
            "P_ASR": False,
            "T_ASR": False,
            "R_ASR": False,
            "STRICT_E2E_ASR": False,
            "timeout": True,
            "runtime_failure": False,
            "duration_seconds": 90.0,
            "raw_log": "response.json",
            "reset_status": 0,
        },
    ]

    result = aggregate_smoke_cases(tmp_path, cases)

    assert result["aggregate"] == summarize_cases(cases)
    assert set(result["models"]) == {"m1", "m2"}
    assert set(result["tasks"]) == {"HumanEval/0"}
    assert result["aggregate"]["timeout_rate"] == 0.5
