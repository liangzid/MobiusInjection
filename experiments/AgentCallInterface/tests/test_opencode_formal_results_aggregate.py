import json

import pytest

from experiments.AgentCallInterface.coding_evaluation.opencode_formal_results_aggregate import (
    load_run_metrics,
    merge_runs,
    write_package,
)


def write_run(root, model_label, cases):
    root.mkdir(parents=True)
    payload = {
        "run_config": {
            "model_label": model_label,
            "model_id": f"provider/{model_label}",
            "limit": len(cases),
        },
        "summary": {},
        "cases": cases,
    }
    (root / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")


def case(model_label, task_id, tsr=True, t_asr=True):
    return {
        "case_id": f"{model_label}_{task_id}",
        "model_label": model_label,
        "task_id": task_id,
        "TSR": tsr,
        "STRICT_TSR": tsr,
        "P_ASR": True,
        "T_ASR": t_asr,
        "R_ASR": False,
        "STRICT_E2E_ASR": False,
        "runner_succeeded": True,
        "verifier_ran": True,
        "verified_tests_passed": 2 if tsr else 1,
        "verified_tests_total": 2,
        "trace_record_count": 7,
        "clean_followup_trace_record_count": 0,
    }


def test_merge_runs_summarizes_across_models(tmp_path):
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    write_run(run_a, "m1", [case("m1", "HumanEval/0"), case("m1", "HumanEval/1", tsr=False)])
    write_run(run_b, "m2", [case("m2", "HumanEval/0", t_asr=False)])

    result = merge_runs([run_a, run_b])

    assert result["summary"]["N"] == 3
    assert result["summary"]["TSR"] == 2 / 3
    assert result["models"]["m1"]["N"] == 2
    assert result["models"]["m2"]["T_ASR"] == 0.0
    assert len(result["runs"]) == 2


def test_write_package_outputs_aggregate_files(tmp_path):
    run_a = tmp_path / "run_a"
    output = tmp_path / "out"
    output.mkdir()
    write_run(run_a, "m1", [case("m1", "HumanEval/0")])
    result = merge_runs([run_a])

    write_package(output, result)

    assert (output / "metrics.json").exists()
    assert (output / "case_metrics.csv").exists()
    assert (output / "model_metrics.csv").exists()
    assert "OpenCode Formal All-Targets" in (output / "metrics_report.md").read_text(
        encoding="utf-8"
    )


def test_load_run_metrics_rejects_missing_metrics(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_run_metrics(tmp_path / "missing_run")
