import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "experiments/scripts/pending_claw_task_ids.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("pending_claw_task_ids", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pending_excludes_completed_and_retries_401(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text("HTTP 401: User not found.\n", encoding="utf-8")
    good_dir = log_dir / "openclaw" / "doc-006" / "poisoned"
    good_dir.mkdir(parents=True)
    (good_dir / "stdout.txt").write_text("rendered the template\n", encoding="utf-8")
    calling = good_dir / "reopened_calling"
    calling.mkdir()
    (calling / "stdout.txt").write_text("HTTP 401 should be ignored here\n", encoding="utf-8")
    rows = [
        {"task_id": "doc-005", "agent": "openclaw"},
        {"task_id": "doc-006", "agent": "openclaw"},
    ]
    (log_dir / "results.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )

    all_ids = ["doc-005", "doc-006", "doc-010"]
    assert module.auth_failed_task_ids(log_dir) == {"doc-005"}
    assert module.completed_task_ids(log_dir) == {"doc-005", "doc-006"}
    assert module.pending_task_ids(all_ids, log_dir) == ["doc-005", "doc-010"]


def test_pending_retries_empty_stdout(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text("", encoding="utf-8")
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "openclaw"}) + "\n",
        encoding="utf-8",
    )
    assert module.empty_stdout_task_ids(log_dir) == {"doc-005"}
    assert module.pending_task_ids(["doc-005"], log_dir) == ["doc-005"]


def test_pending_retries_openclaw_timeout_stderr(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.json").write_text("", encoding="utf-8")
    (task_dir / "stderr.txt").write_text(
        "\n[runner] openclaw agent turn timed out after 440s\n", encoding="utf-8"
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "openclaw"}) + "\n",
        encoding="utf-8",
    )
    assert module.empty_stdout_task_ids(log_dir) == {"doc-005"}
    assert module.pending_task_ids(["doc-005"], log_dir) == ["doc-005"]


def test_pending_keeps_openclaw_stderr_payloads(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "openclaw" / "doc-006" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.json").write_text("", encoding="utf-8")
    (task_dir / "stderr.txt").write_text(
        '{"payloads":[{"text":"rendered the template from data.json"}]}\n',
        encoding="utf-8",
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-006", "agent": "openclaw"}) + "\n",
        encoding="utf-8",
    )
    assert module.empty_stdout_task_ids(log_dir) == set()
    assert module.pending_task_ids(["doc-006"], log_dir) == []


def test_pending_retries_openrouter_transport_error(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "zeroclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text("zeroclaw config loaded\n", encoding="utf-8")
    (task_dir / "stderr.txt").write_text(
        "All providers/models failed. Attempts:\n"
        "provider=openrouter model=qwen/qwen3.6-plus attempt 1/3: "
        "OpenRouter transport error while reading response body\n",
        encoding="utf-8",
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "zeroclaw"}) + "\n",
        encoding="utf-8",
    )
    assert module.empty_stdout_task_ids(log_dir) == {"doc-005"}
    assert module.pending_task_ids(["doc-005"], log_dir) == ["doc-005"]


def test_pending_is_all_ids_when_log_dir_missing(tmp_path: Path) -> None:
    module = _load()
    all_ids = ["doc-005", "doc-006"]
    assert module.pending_task_ids(all_ids, tmp_path / "missing") == all_ids


def test_pending_retries_caller_success_false(tmp_path: Path) -> None:
    module = _load()
    log_dir = tmp_path / "run"
    task_dir = log_dir / "zeroclaw" / "doc-005" / "poisoned"
    task_dir.mkdir(parents=True)
    (task_dir / "stdout.txt").write_text(
        "zeroclaw config loaded and memory initialized\n", encoding="utf-8"
    )
    (log_dir / "results.jsonl").write_text(
        json.dumps({"task_id": "doc-005", "agent": "zeroclaw", "caller_success": False})
        + "\n",
        encoding="utf-8",
    )
    assert module.failed_caller_task_ids(log_dir) == {"doc-005"}
    assert module.pending_task_ids(["doc-005"], log_dir) == ["doc-005"]
