"""Aggregate benchmark case metrics into JSON, CSV, and Markdown summaries."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def aggregate_benchmark_run(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    manifest = _read_manifest(run_path)
    cases = [_case_summary(run_path, entry) for entry in manifest]
    summary = _summary(cases)
    result = {"run_dir": str(run_path), "summary": summary, "cases": cases}
    _write_outputs(run_path, result)
    return result


def _read_manifest(run_path: Path) -> list[dict[str, Any]]:
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        return []
    return json.loads(manifest_path.read_text())


def _case_summary(run_path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    metrics = _read_json(entry.get("metrics_file"))
    analysis = _read_json(entry.get("analysis_file"))
    indicators = _merged_indicators(metrics, analysis)
    counters = _merged_counters(metrics, analysis)
    incomplete = metrics is None or analysis is None
    return {
        "benchmark_id": entry.get("benchmark_id", ""),
        "dataset": entry.get("dataset", ""),
        "task_id": entry.get("task_id", ""),
        "agent": entry.get("agent", ""),
        "model": entry.get("model", ""),
        "prompt_order": entry.get("prompt_order", ""),
        "status": "incomplete" if incomplete else "completed",
        "metrics_file": entry.get("metrics_file", ""),
        "analysis_file": entry.get("analysis_file", ""),
        "runner_succeeded": bool(indicators.get("runner_succeeded", False)),
        "skill_injected": bool(indicators.get("skill_injected", False)),
        "skills_visible": bool(indicators.get("skills_visible_post", False)),
        "recursive_triggered": bool(indicators.get("recursive_triggered", False)),
        "runtime_failure": bool(indicators.get("runtime_failure_detected", False)),
        "timeout": bool(indicators.get("active_after_timeout", False)),
        "persistence_markers": int(counters.get("persistence_markers", 0) or 0),
    }


def _read_json(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _merged_indicators(
    metrics: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    indicators: dict[str, Any] = {}
    if metrics:
        indicators.update(metrics.get("indicators", {}))
    if analysis:
        indicators.update(analysis.get("indicators", {}))
    return indicators


def _merged_counters(
    metrics: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    counters: dict[str, Any] = {}
    if metrics:
        counters.update(metrics.get("counters", {}))
    if analysis:
        counters.update(analysis.get("counters", {}))
    return counters


def _summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(cases)
    completed = sum(case["status"] == "completed" for case in cases)
    return {
        "total_cases": total,
        "completed_cases": completed,
        "runner_success_rate": _rate(cases, "runner_succeeded"),
        "injection_hit_rate": _rate(cases, "skill_injected"),
        "skills_visible_rate": _rate(cases, "skills_visible"),
        "persistence_rate": _predicate_rate(cases, lambda case: case["persistence_markers"] > 0),
        "recursive_trigger_rate": _rate(cases, "recursive_triggered"),
        "timeout_count": sum(case["timeout"] for case in cases),
        "runtime_failure_count": sum(case["runtime_failure"] for case in cases),
        "per_agent": _breakdown(cases, "agent"),
        "per_task": _breakdown(cases, "task_id"),
    }


def _rate(cases: list[dict[str, Any]], key: str) -> float:
    return _predicate_rate(cases, lambda case: bool(case[key]))


def _predicate_rate(cases: list[dict[str, Any]], predicate) -> float:
    completed = [case for case in cases if case["status"] == "completed"]
    if not completed:
        return 0.0
    return sum(1 for case in completed if predicate(case)) / len(completed)


def _breakdown(cases: list[dict[str, Any]], key: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[str(case[key])].append(case)
    return {name: _small_summary(items) for name, items in sorted(grouped.items())}


def _small_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_cases": len(cases),
        "completed_cases": sum(case["status"] == "completed" for case in cases),
        "runner_success_rate": _rate(cases, "runner_succeeded"),
        "injection_hit_rate": _rate(cases, "skill_injected"),
        "skills_visible_rate": _rate(cases, "skills_visible"),
        "persistence_rate": _predicate_rate(cases, lambda case: case["persistence_markers"] > 0),
        "recursive_trigger_rate": _rate(cases, "recursive_triggered"),
    }


def _write_outputs(run_path: Path, result: dict[str, Any]) -> None:
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "benchmark_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    _write_csv(run_path / "benchmark_summary.csv", result["cases"])
    _write_markdown(run_path / "benchmark_report.md", result)


def _write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    fieldnames = [
        "benchmark_id",
        "dataset",
        "task_id",
        "agent",
        "model",
        "status",
        "runner_succeeded",
        "skill_injected",
        "skills_visible",
        "persistence_markers",
        "recursive_triggered",
        "timeout",
        "runtime_failure",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow({key: case.get(key, "") for key in fieldnames})


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    lines = [
        "# Benchmark Report",
        "",
        f"Total cases: {summary['total_cases']}",
        f"Completed cases: {summary['completed_cases']}",
        f"Runner success rate: {summary['runner_success_rate']:.3f}",
        f"Injection hit rate: {summary['injection_hit_rate']:.3f}",
        f"Skills visible rate: {summary['skills_visible_rate']:.3f}",
        f"Persistence rate: {summary['persistence_rate']:.3f}",
        f"Recursive trigger rate: {summary['recursive_trigger_rate']:.3f}",
        f"Timeout count: {summary['timeout_count']}",
        f"Runtime failure count: {summary['runtime_failure_count']}",
        "",
        "## Cases",
        "",
        "| Benchmark | Task | Agent | Status | Runner | Injection | Skills Visible | Persistence |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for case in result["cases"]:
        lines.append(_case_markdown_row(case))
    path.write_text("\n".join(lines) + "\n")


def _case_markdown_row(case: dict[str, Any]) -> str:
    return (
        f"| {case['benchmark_id']} | {case['task_id']} | {case['agent']} | "
        f"{case['status']} | {case['runner_succeeded']} | {case['skill_injected']} | "
        f"{case['skills_visible']} | {case['persistence_markers']} |"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = aggregate_benchmark_run(args.run_dir)
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
