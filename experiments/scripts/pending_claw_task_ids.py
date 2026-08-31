#!/usr/bin/env python3
"""Return Claw task IDs that still need a non-401 run in a log directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _task_id_from_stdout_path(path: Path) -> str | None:
    parts = path.parts
    if "poisoned" not in parts:
        return None
    if path.name not in {"stdout.txt", "stdout.json", "stderr.txt"}:
        return None
    if "reopened_calling" in parts:
        return None
    try:
        poisoned_idx = parts.index("poisoned")
    except ValueError:
        return None
    if poisoned_idx < 1:
        return None
    return parts[poisoned_idx - 1]


def _poisoned_dirs(log_dir: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    if not log_dir.exists():
        return found
    for poisoned in log_dir.rglob("poisoned"):
        if not poisoned.is_dir() or poisoned.name != "poisoned":
            continue
        if "reopened_calling" in poisoned.parts:
            continue
        found.append((poisoned.parent.name, poisoned))
    return found


def _trace_text(poisoned: Path) -> str:
    chunks: list[str] = []
    for name in ("stdout.txt", "stdout.json", "stderr.txt"):
        path = poisoned / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _trace_is_empty(text: str) -> bool:
    if '"payloads"' in text:
        return False
    if "[runner]" in text and "timed out" in text:
        return True
    if "All providers/models failed" in text:
        return True
    return not text.strip()


def auth_failed_task_ids(log_dir: Path) -> set[str]:
    failed: set[str] = set()
    for task_id, poisoned in _poisoned_dirs(log_dir):
        text = _trace_text(poisoned)
        if "HTTP 401" in text or "User not found" in text:
            failed.add(task_id)
    return failed


def completed_task_ids(log_dir: Path) -> set[str]:
    completed: set[str] = set()
    results = log_dir / "results.jsonl"
    if not results.exists():
        return completed
    for line in results.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        task_id = row.get("task_id")
        if task_id:
            completed.add(str(task_id))
    return completed


def empty_stdout_task_ids(log_dir: Path) -> set[str]:
    empty: set[str] = set()
    seen: set[str] = set()
    for task_id, poisoned in _poisoned_dirs(log_dir):
        seen.add(task_id)
        if _trace_is_empty(_trace_text(poisoned)):
            empty.add(task_id)
    for task_id in completed_task_ids(log_dir):
        if task_id not in seen:
            empty.add(task_id)
    return empty


def failed_caller_task_ids(log_dir: Path) -> set[str]:
    last: dict[str, bool | None] = {}
    results = log_dir / "results.jsonl"
    if not results.exists():
        return set()
    for line in results.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        task_id = row.get("task_id")
        if task_id:
            last[str(task_id)] = row.get("caller_success")
    return {task_id for task_id, success in last.items() if success is False}


def pending_task_ids(all_ids: list[str], log_dir: Path) -> list[str]:
    keep = (
        completed_task_ids(log_dir)
        - auth_failed_task_ids(log_dir)
        - empty_stdout_task_ids(log_dir)
        - failed_caller_task_ids(log_dir)
    )
    return [task_id for task_id in all_ids if task_id not in keep]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("task_ids", nargs="+")
    args = parser.parse_args()
    pending = pending_task_ids(args.task_ids, Path(args.log_dir))
    print(" ".join(pending))


if __name__ == "__main__":
    main()
