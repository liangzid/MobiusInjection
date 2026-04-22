from pathlib import Path

from experiments.AgentCallInterface.datasets.coding_benchmark_loader import (
    load_benchmark_tasks,
)
from experiments.AgentCallInterface.evaluation.benchmark_manifest import (
    build_benchmark_manifest,
    sanitize_path_segment,
)


def test_benchmark_manifest_is_deterministic(tmp_path):
    tasks = load_benchmark_tasks(dataset="humaneval", limit=2)
    agents = ["opencode", "kilo_code"]

    first = build_benchmark_manifest(tasks, agents, "model-a", tmp_path)
    second = build_benchmark_manifest(tasks, agents, "model-a", tmp_path)

    assert first == second


def test_benchmark_manifest_builds_task_agent_product(tmp_path):
    tasks = load_benchmark_tasks(dataset="humaneval", limit=2)
    entries = build_benchmark_manifest(tasks, ["opencode", "claude_code"], "model-a", tmp_path)

    assert len(entries) == 4
    assert {entry.agent for entry in entries} == {"opencode", "claude_code"}
    assert {entry.task_id for entry in entries} == {"HumanEval/0", "HumanEval/1"}


def test_benchmark_manifest_sanitizes_task_ids_in_paths(tmp_path):
    tasks = load_benchmark_tasks(dataset="humaneval", limit=1)
    entry = build_benchmark_manifest(tasks, ["opencode"], "model-a", tmp_path)[0]

    assert sanitize_path_segment("HumanEval/0") == "HumanEval_0"
    assert "HumanEval_0" in Path(entry.output_prefix).as_posix()
    assert "HumanEval/0" not in Path(entry.output_prefix).as_posix()
