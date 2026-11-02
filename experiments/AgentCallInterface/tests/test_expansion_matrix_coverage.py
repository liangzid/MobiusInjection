import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "experiments/scripts/expansion_matrix_coverage.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("expansion_matrix_coverage", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expected_counts() -> None:
    module = _load()
    expected = module.expected_counts()
    assert expected["humaneval_add_s"] == 492
    assert expected["humaneval_edit_s"] == 492
    assert expected["swebench_add_s"] == 240
    assert expected["swebench_edit_s"] == 240
    assert expected["claw_orig_11"] == 792
    assert expected["claw_new_28"] == 504


def test_classify_coding_stdout() -> None:
    module = _load()
    assert module.classify_coding_stdout("HTTP 401: User not found.\n") == "invalid_401"
    assert module.classify_coding_stdout("short") == "invalid_empty"
    assert module.classify_coding_stdout("x" * 200) == "ok"


def test_coding_cell_status_requires_metrics(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output = log_dir / "humaneval_HumanEval_20_opencode_abc_opencode_output.txt"
    output.write_text("x" * 250, encoding="utf-8")
    assert module.coding_cell_status([log_dir], "HumanEval_20", "opencode") == "present_no_asr"
    metrics = log_dir / "humaneval_HumanEval_20_opencode_abc_opencode_metrics.json"
    metrics.write_text("{}", encoding="utf-8")
    assert module.coding_cell_status([log_dir], "HumanEval_20", "opencode") == "valid"
    assert module.coding_cell_status([log_dir], "HumanEval_2", "opencode") == "missing"


def test_claw_new_c_dirs_match_batch_agent_suffix() -> None:
    module = _load()
    for strategy in ("add_c", "edit_c"):
        for agent in module.CLAW_AGENTS:
            paths = module.CLAW_NEW_DIRS[(strategy, agent)]
            assert len(paths) == 1
            assert paths[0].name.endswith(f"_{agent}"), paths[0].name


def test_claw_cell_retries_401(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text("HTTP 401: User not found.\n", encoding="utf-8")
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "openclaw", "injection_observed": False})
        + "\n",
        encoding="utf-8",
    )
    (log_dir / "calling_results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "openclaw", "skill_started": False}) + "\n",
        encoding="utf-8",
    )
    assert module.claw_cell_status([log_dir], "openclaw", "doc-005") == "invalid_401"
    (task_dir / "stdout.txt").write_text("", encoding="utf-8")
    assert module.claw_cell_status([log_dir], "openclaw", "doc-005") == "valid"
    assert (
        module.claw_cell_status(
            [log_dir], "openclaw", "doc-005", require_nonempty_stdout=True
        )
        == "invalid_empty"
    )
    (task_dir / "stdout.txt").write_text("rendered the template\n", encoding="utf-8")
    assert module.claw_cell_status([log_dir], "openclaw", "doc-005") == "valid"
    assert module.claw_cell_status([log_dir], "openclaw", "doc-006") == "missing"


def test_claw_cell_accepts_openclaw_stderr_payloads(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-006" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.json").write_text("", encoding="utf-8")
    (task_dir / "stderr.txt").write_text(
        '{"payloads":[{"text":"rendered the template"}]}\n', encoding="utf-8"
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-006", "agent": "openclaw", "injection_observed": True})
        + "\n",
        encoding="utf-8",
    )
    (log_dir / "calling_results.jsonl").write_text(
        json.dumps({"task_id": "doc-006", "agent": "openclaw", "skill_started": False}) + "\n",
        encoding="utf-8",
    )
    assert (
        module.claw_cell_status(
            [log_dir], "openclaw", "doc-006", require_nonempty_stdout=True
        )
        == "valid"
    )
    (task_dir / "stderr.txt").write_text(
        "\n[runner] openclaw agent turn timed out after 440s\n", encoding="utf-8"
    )
    assert (
        module.claw_cell_status(
            [log_dir], "openclaw", "doc-006", require_nonempty_stdout=True
        )
        == "invalid_empty"
    )


def test_claw_cell_retries_provider_failed(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "zeroclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text("zeroclaw config loaded\n", encoding="utf-8")
    (task_dir / "stderr.txt").write_text(
        "All providers/models failed. Attempts:\n"
        "provider=openrouter model=qwen/qwen3.6-plus attempt 1/3: retryable\n",
        encoding="utf-8",
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "zeroclaw", "injection_observed": True})
        + "\n",
        encoding="utf-8",
    )
    (log_dir / "calling_results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "zeroclaw", "skill_started": False})
        + "\n",
        encoding="utf-8",
    )
    assert (
        module.claw_cell_status(
            [log_dir], "zeroclaw", "doc-005", require_nonempty_stdout=True
        )
        == "invalid_empty"
    )


def test_claw_cell_retries_caller_success_false(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "zeroclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text(
        "zeroclaw config loaded and memory initialized\n", encoding="utf-8"
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps(
            {
                "task_id": "doc-005",
                "agent": "zeroclaw",
                "caller_success": False,
                "injection_observed": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (log_dir / "calling_results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "zeroclaw", "skill_started": False})
        + "\n",
        encoding="utf-8",
    )
    assert (
        module.claw_cell_status(
            [log_dir], "zeroclaw", "doc-005", require_nonempty_stdout=True
        )
        == "invalid_empty"
    )
