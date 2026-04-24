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


@dataclass(frozen=True)
class BenchmarkTask:
    dataset: str
    task_id: str
    prompt: str
    entry_point: str
    metadata: dict[str, Any] = field(default_factory=dict)


HUMANEVAL_TASK_INSTRUCTIONS = """You are completing a HumanEval Python programming task.

The task content below contains the required imports, function signature, and
docstring. Implement the function described by the docstring. Preserve the
function signature and make the implementation pass the examples and hidden
tests for the named entry point. Do not ask follow-up questions; complete the
task in this run.

Task content:
"""

SWEBENCH_TASK_INSTRUCTIONS = """You are completing a SWE-bench software engineering task.

Use the issue description, repository metadata, and test patch below to infer the
required code change. Make the smallest correct fix that would satisfy the
tests. Do not ask follow-up questions; complete the task in this run.

"""


def build_humaneval_benchmark_prompt(prompt: str, entry_point: str) -> str:
    entry_point_line = f"Entry point: {entry_point}\n\n" if entry_point else ""
    return f"{HUMANEVAL_TASK_INSTRUCTIONS}{entry_point_line}{prompt}"


def build_swebench_benchmark_prompt(task: CodingTask) -> str:
    sections = [
        SWEBENCH_TASK_INSTRUCTIONS,
        f"Repository: {task.repo}",
        f"Instance ID: {task.instance_id or task.task_id}",
        f"Repository version: {task.repo_version}",
        "",
        "Issue description:",
        task.problem_statement,
    ]
    if task.hints:
        sections.extend(["", "Hints:", task.hints])
    if task.test_patch:
        sections.extend(["", "Test patch:", task.test_patch])
    return "\n".join(sections).strip() + "\n"


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

    def load_benchmark_tasks(
        self,
        limit: int | None = None,
        offset: int = 0,
        task_ids: list[str] | None = None,
        dataset_type: str = "verified_mini",
    ) -> list[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                dataset="swebench",
                task_id=task.task_id,
                prompt=build_swebench_benchmark_prompt(task),
                entry_point="",
                metadata={
                    **task.metadata,
                    "benchmark_prompt_kind": "swebench_issue_v1",
                    "repo": task.repo,
                    "instance_id": task.instance_id,
                    "repo_version": task.repo_version,
                    "has_test_patch": bool(task.test_patch),
                },
            )
            for task in self.load_tasks(dataset_type=dataset_type)
        ]
        return filter_benchmark_tasks(tasks, limit=limit, offset=offset, task_ids=task_ids)

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

        data_file = self._resolve_data_file()
        tasks = self._parse_humaneval(data_file)
        self._tasks_cache = tasks
        return tasks

    def load_benchmark_tasks(
        self,
        limit: int | None = None,
        offset: int = 0,
        task_ids: list[str] | None = None,
    ) -> list[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                dataset="humaneval",
                task_id=task.task_id,
                prompt=build_humaneval_benchmark_prompt(task.prompt, task.entry_point),
                entry_point=task.entry_point,
                metadata={
                    **task.metadata,
                    "benchmark_prompt_kind": "humaneval_completion_v1",
                    "raw_prompt_length": len(task.prompt),
                },
            )
            for task in self.load_tasks()
        ]
        return filter_benchmark_tasks(tasks, limit=limit, offset=offset, task_ids=task_ids)

    def _resolve_data_file(self) -> Path:
        candidates = [
            self.data_dir / "HumanEval.jsonl",
            Path(__file__).parent / "HumanEval.jsonl",
            self.data_dir / "humaneval_data.json",
            Path(__file__).parent / "humaneval_data" / "humaneval_data.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "HumanEval data file not found. Expected an existing repo fixture, "
            "for example experiments/AgentCallInterface/datasets/HumanEval.jsonl."
        )

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
            data = self._read_records(data_file)
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

    def _read_records(self, data_file: Path) -> list[dict[str, Any]]:
        text = data_file.read_text()
        if data_file.suffix == ".jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return []


class CodingBenchmarkLoader:
    def __init__(self, data_dir: Path | str | None = None):
        self.swebench = SWEBenchLoader(data_dir)
        self.humaneval = HumanEvalLoader(data_dir)

    def load_swebench(self, **kwargs) -> list[CodingTask]:
        return self.swebench.load_tasks(**kwargs)

    def load_humaneval(self, **kwargs) -> list[HumanEvalTask]:
        return self.humaneval.load_tasks(**kwargs)

    def load_benchmark_tasks(
        self,
        dataset: str = "humaneval",
        limit: int | None = None,
        offset: int = 0,
        task_ids: list[str] | None = None,
    ) -> list[BenchmarkTask]:
        normalized = dataset.lower()
        if normalized in {"humaneval", "human_eval", "human-eval"}:
            return self.humaneval.load_benchmark_tasks(
                limit=limit,
                offset=offset,
                task_ids=task_ids,
            )
        if normalized in {"swebench", "swe-bench", "swe_bench"}:
            return self.swebench.load_benchmark_tasks(
                limit=limit,
                offset=offset,
                task_ids=task_ids,
            )
        raise ValueError(f"Unsupported benchmark dataset: {dataset}")

    def to_agent_input(self, task: CodingTask, agent_type: str) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "instance_id": task.instance_id,
            "agent_type": agent_type,
            "repo": task.repo,
            "problem_statement": task.problem_statement,
            "test_patch": task.test_patch,
        }


def filter_benchmark_tasks(
    tasks: list[BenchmarkTask],
    limit: int | None = None,
    offset: int = 0,
    task_ids: list[str] | None = None,
) -> list[BenchmarkTask]:
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative")
    if task_ids is not None:
        requested = set(task_ids)
        tasks = [task for task in tasks if task.task_id in requested]
    if offset:
        tasks = tasks[offset:]
    if limit is not None:
        tasks = tasks[:limit]
    return tasks


def load_benchmark_tasks(
    dataset: str = "humaneval",
    limit: int | None = None,
    offset: int = 0,
    task_ids: list[str] | None = None,
    data_dir: Path | str | None = None,
) -> list[BenchmarkTask]:
    normalized = dataset.lower()
    if normalized in {"humaneval", "human_eval", "human-eval"}:
        loader = HumanEvalLoader(data_dir=data_dir)
        return loader.load_benchmark_tasks(limit=limit, offset=offset, task_ids=task_ids)
    if normalized in {"swebench", "swe-bench", "swe_bench"}:
        loader = SWEBenchLoader(data_dir=data_dir)
        return loader.load_benchmark_tasks(limit=limit, offset=offset, task_ids=task_ids)
    raise ValueError(f"Unsupported benchmark dataset: {dataset}")


if __name__ == "__main__":
    loader = SWEBenchLoader()
    tasks = loader.load_tasks()
    print(f"Loaded {len(tasks)} tasks from SWE-Bench")
