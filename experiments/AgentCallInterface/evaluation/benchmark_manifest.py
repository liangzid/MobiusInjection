"""Build deterministic benchmark manifests for coding-agent evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from experiments.AgentCallInterface.datasets.coding_benchmark_loader import (
    BenchmarkTask,
    load_benchmark_tasks,
)
from experiments.AgentCallInterface.evaluation.prompt_composer import SUPPORTED_ORDER


SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class BenchmarkManifestEntry:
    benchmark_id: str
    dataset: str
    task_id: str
    agent: str
    model: str
    prompt_order: str
    status: str
    output_prefix: str
    entry_point: str
    task_prompt_file: str
    metrics_file: str
    analysis_file: str
    output_file: str
    followup_file: str
    injection_file: str
    log_file: str


def sanitize_path_segment(value: str) -> str:
    sanitized = SAFE_SEGMENT_RE.sub("_", value).strip("._")
    return sanitized or "item"


def deterministic_benchmark_id(
    dataset: str,
    task_id: str,
    agent: str,
    model: str,
    prompt_order: str,
) -> str:
    payload = "\n".join([dataset, task_id, agent, model, prompt_order])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    task_part = sanitize_path_segment(task_id)
    agent_part = sanitize_path_segment(agent)
    return f"{dataset}_{task_part}_{agent_part}_{digest}"


def build_benchmark_manifest(
    tasks: Iterable[BenchmarkTask],
    agents: Iterable[str],
    model: str,
    run_dir: str | Path,
    prompt_order: str = SUPPORTED_ORDER,
) -> list[BenchmarkManifestEntry]:
    run_path = Path(run_dir)
    entries: list[BenchmarkManifestEntry] = []
    for task in tasks:
        prompt_file = run_path / "task_prompts" / f"{sanitize_path_segment(task.task_id)}.txt"
        for agent in agents:
            entries.append(_build_entry(task, agent, model, prompt_order, run_path, prompt_file))
    return entries


def write_manifest(entries: list[BenchmarkManifestEntry], manifest_path: str | Path) -> None:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(entry) for entry in entries]
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_task_prompt_files(tasks: Iterable[BenchmarkTask], run_dir: str | Path) -> None:
    prompt_dir = Path(run_dir) / "task_prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        prompt_path = prompt_dir / f"{sanitize_path_segment(task.task_id)}.txt"
        prompt_path.write_text(task.prompt, encoding="utf-8")


def _build_entry(
    task: BenchmarkTask,
    agent: str,
    model: str,
    prompt_order: str,
    run_path: Path,
    prompt_file: Path,
) -> BenchmarkManifestEntry:
    benchmark_id = deterministic_benchmark_id(
        task.dataset, task.task_id, agent, model, prompt_order
    )
    output_prefix = run_path / "cases" / sanitize_path_segment(task.task_id) / agent / benchmark_id
    log_prefix = run_path / "logs" / f"{benchmark_id}_{agent}"
    return BenchmarkManifestEntry(
        benchmark_id=benchmark_id,
        dataset=task.dataset,
        task_id=task.task_id,
        agent=agent,
        model=model,
        prompt_order=prompt_order,
        status="pending",
        output_prefix=str(output_prefix),
        entry_point=task.entry_point,
        task_prompt_file=str(prompt_file),
        metrics_file=f"{log_prefix}_metrics.json",
        analysis_file=f"{log_prefix}_analysis.json",
        output_file=f"{log_prefix}_output.txt",
        followup_file=f"{log_prefix}_followup.txt",
        injection_file=f"{log_prefix}_injection.txt",
        log_file=str(run_path / "logs" / f"{benchmark_id}.log"),
    )


def _parse_agents(raw_agents: str) -> list[str]:
    return [agent.strip() for agent in raw_agents.split(",") if agent.strip()]


def _parse_task_ids(raw_task_ids: str | None) -> list[str] | None:
    if raw_task_ids is None:
        return None
    return [task_id.strip() for task_id in raw_task_ids.split(",") if task_id.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="humaneval")
    parser.add_argument("--model", required=True)
    parser.add_argument("--agents", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--prompt-order", default=SUPPORTED_ORDER)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--task-ids")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_benchmark_tasks(
        dataset=args.dataset,
        limit=args.limit,
        offset=args.offset,
        task_ids=_parse_task_ids(args.task_ids),
    )
    agents = _parse_agents(args.agents)
    write_task_prompt_files(tasks, args.run_dir)
    entries = build_benchmark_manifest(tasks, agents, args.model, args.run_dir, args.prompt_order)
    write_manifest(entries, args.manifest)
    print(json.dumps({"manifest": args.manifest, "cases": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
