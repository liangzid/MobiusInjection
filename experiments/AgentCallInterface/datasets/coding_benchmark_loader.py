"""
Coding Benchmark Dataset Loader
==============================
Loads and processes coding benchmarks for evaluating coding-style agents.

Datasets:
- SWE-bench Lite (300 instances) - loaded from HuggingFace: SWE-bench/SWE-bench_Lite
- SWE-bench Full (train split available)
- HumanEval (164 Python coding problems)

Agents evaluated: claude code, cursor, opencode, kilo code, codex, droid, zed
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CodingTask:
    dataset: str
    task_id: str
    instance_id: str
    repo: str
    problem_statement: str
    hints: str
    created_at: str
    test_patch: str
    repo_version: str
    hw_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanEvalTask:
    task_id: str
    prompt: str
    canonical_solution: str
    test: str
    entry_point: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SWEBenchLoader:
    DEFAULT_REPO = "https://github.com/princeton-nlp/SWE-bench.git"
    VERIFIED_MINI_URL = "https://huggingface.co/datasets/princeton-nlp/SWE-bench/resolve/main/swebench_verified_mini.json"

    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir) if data_dir else self._get_default_data_dir()
        self._tasks_cache: list[CodingTask] | None = None

    def _get_default_data_dir(self) -> Path:
        return Path(__file__).parent / "swebench_data"

    def load_tasks(
        self,
        dataset_type: str = "verified_mini",
        repos: list[str] | None = None,
    ) -> list[CodingTask]:
        cache_key = f"{dataset_type}_{'-'.join(repos) if repos else 'all'}"
        if self._tasks_cache is not None:
            return self._filter_tasks(self._tasks_cache, repos)

        data_file = self.data_dir / f"{dataset_type}.json"
        if not data_file.exists():
            self._download_dataset(dataset_type)

        tasks = self._parse_swebench(data_file)
        self._tasks_cache = tasks
        return self._filter_tasks(tasks, repos)

    def _filter_tasks(
        self, tasks: list[CodingTask], repos: list[str] | None
    ) -> list[CodingTask]:
        if not repos:
            return tasks
        return [t for t in tasks if t.repo in repos]

    def _download_dataset(self, dataset_type: str) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.data_dir / f"{dataset_type}.json"
        subprocess.run(
            ["curl", "-L", "-o", str(output_file), self.VERIFIED_MINI_URL],
            capture_output=True,
            check=True,
        )

    def _parse_swebench(self, data_file: Path) -> list[CodingTask]:
        tasks: list[CodingTask] = []
        try:
            data = json.loads(data_file.read_text())
            if isinstance(data, list):
                for item in data:
                    task = CodingTask(
                        dataset="SWE-Bench",
                        task_id=item.get("instance_id", item.get("id", "")),
                        instance_id=item.get("instance_id", ""),
                        repo=item.get("repo", ""),
                        problem_statement=item.get("problem_statement", ""),
                        hints=item.get("hints", ""),
                        created_at=item.get("created_at", ""),
                        test_patch=item.get("test_patch", ""),
                        repo_version=item.get("repo_version", ""),
                        hw_cost=item.get("HW_COST", 0.0),
                        metadata=item,
                    )
                    tasks.append(task)
        except json.JSONDecodeError:
            pass
        return tasks


class HumanEvalLoader:
    DEFAULT_URL = (
        "https://huggingface.co/datasets/openai/human-eval/resolve/main/data.json"
    )

    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir) if data_dir else self._get_default_data_dir()
        self._tasks_cache: list[HumanEvalTask] | None = None

    def _get_default_data_dir(self) -> Path:
        return Path(__file__).parent / "humaneval_data"

    def load_tasks(self) -> list[HumanEvalTask]:
        if self._tasks_cache is not None:
            return self._tasks_cache

        data_file = self.data_dir / "humaneval_data.json"
        if not data_file.exists():
            self._download_dataset()

        tasks = self._parse_humaneval(data_file)
        self._tasks_cache = tasks
        return tasks

    def _download_dataset(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.data_dir / "humaneval_data.json"
        subprocess.run(
            ["curl", "-L", "-o", str(output_file), self.DEFAULT_URL],
            capture_output=True,
            check=True,
        )

    def _parse_humaneval(self, data_file: Path) -> list[HumanEvalTask]:
        tasks: list[HumanEvalTask] = []
        try:
            data = json.loads(data_file.read_text())
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    task = HumanEvalTask(
                        task_id=item.get("task_id", f"humaneval-{idx}"),
                        prompt=item.get("prompt", ""),
                        canonical_solution=item.get("canonical_solution", ""),
                        test=item.get("test", ""),
                        entry_point=item.get("entry_point", ""),
                        metadata=item,
                    )
                    tasks.append(task)
        except json.JSONDecodeError:
            pass
        return tasks


class CodingBenchmarkLoader:
    def __init__(self, data_dir: Path | str | None = None):
        self.swebench = SWEBenchLoader(data_dir)
        self.humaneval = HumanEvalLoader(data_dir)

    def load_swebench(self, **kwargs) -> list[CodingTask]:
        return self.swebench.load_tasks(**kwargs)

    def load_humaneval(self, **kwargs) -> list[HumanEvalTask]:
        return self.humaneval.load_tasks(**kwargs)

    def to_agent_input(self, task: CodingTask, agent_type: str) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "instance_id": task.instance_id,
            "agent_type": agent_type,
            "repo": task.repo,
            "problem_statement": task.problem_statement,
            "test_patch": task.test_patch,
        }


if __name__ == "__main__":
    loader = SWEBenchLoader()
    tasks = loader.load_tasks()
    print(f"Loaded {len(tasks)} tasks from SWE-Bench")
