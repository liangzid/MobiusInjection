"""
ClawBench Dataset Loader
========================
Loads and processes the ClawBench benchmark for evaluating claw-style agents.
Reference: https://github.com/claw-bench/claw-bench

Agents evaluated: openclaw, zeroclaw, nanobot, hermes agent
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClawBenchTask:
    task_id: str
    domain: str
    difficulty: str
    instructions: str
    skill_file: str
    verifier_path: str
    weight: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ClawBenchLoader:
    DEFAULT_SKILL_URL = "https://clawbench.net/skill.md"

    def __init__(self, tasks_dir: Path | str | None = None):
        self.tasks_dir = Path(tasks_dir) if tasks_dir else self._get_default_tasks_dir()
        self._tasks_cache: list[ClawBenchTask] | None = None

    def _get_default_tasks_dir(self) -> Path:
        return Path(__file__).parent / "clawbench_tasks"

    def load_tasks(self, domains: list[str] | None = None, difficulty: list[str] | None = None) -> list[ClawBenchTask]:
        if self._tasks_cache is not None:
            return self._filter_tasks(self._tasks_cache, domains, difficulty)

        if not self.tasks_dir.exists():
            self._clone_and_extract_tasks()

        tasks = self._parse_tasks_from_dir()
        self._tasks_cache = tasks
        return self._filter_tasks(tasks, domains, difficulty)

    def _filter_tasks(
        self,
        tasks: list[ClawBenchTask],
        domains: list[str] | None,
        difficulty: list[str] | None,
    ) -> list[ClawBenchTask]:
        filtered = tasks
        if domains:
            filtered = [t for t in filtered if t.domain.lower() in [d.lower() for d in domains]]
        if difficulty:
            filtered = [t for t in filtered if t.difficulty.upper() in [d.upper() for d in difficulty]]
        return filtered

    def _clone_and_extract_tasks(self) -> None:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        repo_url = "https://github.com/claw-bench/claw-bench.git"
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(self.tasks_dir)],
            capture_output=True,
            check=True,
        )
        clawbench_src = self.tasks_dir / "claw-bench"
        if clawbench_src.exists():
            for item in clawbench_src.iterdir():
                if item.is_dir():
                    (self.tasks_dir / item.name).write_bytes(item.read_bytes())

    def _parse_tasks_from_dir(self) -> list[ClawBenchTask]:
        tasks: list[ClawBenchTask] = []
        tasks_subdir = self.tasks_dir / "tasks"
        if not tasks_subdir.exists():
            return tasks

        for task_file in tasks_subdir.rglob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())
                task = ClawBenchTask(
                    task_id=task_data.get("task_id", task_file.stem),
                    domain=task_data.get("domain", "unknown"),
                    difficulty=task_data.get("difficulty", "L1"),
                    instructions=task_data.get("instructions", ""),
                    skill_file=task_data.get("skill_file", self.DEFAULT_SKILL_URL),
                    verifier_path=task_data.get("verifier", ""),
                    weight=task_data.get("weight", 1),
                    metadata=task_data,
                )
                tasks.append(task)
            except (json.JSONDecodeError, KeyError):
                continue
        return tasks

    def get_quick_test_tasks(self) -> list[ClawBenchTask]:
        quick_test_ids = [
            "file-002", "code-002", "eml-001", "data-002", "debug-001",
            "cal-006", "doc-004", "sys-004", "sec-004", "wfl-003",
            "db-002", "tool-002", "web-006", "mem-005", "xdom-001",
            "plan-004", "math-004", "code-014", "debug-005", "tool-005",
        ]
        all_tasks = self.load_tasks()
        return [t for t in all_tasks if t.task_id in quick_test_ids]

    def to_agent_input(self, task: ClawBenchTask, agent_type: str) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "agent_type": agent_type,
            "skill_url": task.skill_file,
            "task_instructions": task.instructions,
        }


if __name__ == "__main__":
    loader = ClawBenchLoader()
    tasks = loader.load_tasks()
    print(f"Loaded {len(tasks)} tasks from ClawBench")
    quick_tasks = loader.get_quick_test_tasks()
    print(f"Quick test subset: {len(quick_tasks)} tasks")
