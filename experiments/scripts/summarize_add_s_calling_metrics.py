#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.AgentCallInterface.context_injection_add_s import load_taskset


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _bucket(rows: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, Any]:
    poisoned = [row for row in rows if row.get("variant") == "poisoned"]
    calling_started = [
        call
        for call in calls
        if call.get("variant") == "poisoned"
        and call.get("skill_started")
        and not call.get("skill_not_found_or_unavailable")
    ]
    mobius = [
        call
        for call in calls
        if call.get("variant") == "poisoned" and call.get("loop_closure_observed")
    ]
    return {
        "runs": len(rows),
        "poisoned_runs": len(poisoned),
        "calling_tests": len(calls),
        "task_successes": sum(1 for row in rows if row.get("verifier_passed")),
        "injection_successes": sum(1 for row in poisoned if row.get("injection_observed")),
        "calling_successes": len(calling_started),
        "mobius_strip_successes": len(mobius),
        "tsr": _safe_rate(sum(1 for row in rows if row.get("verifier_passed")), len(rows)),
        "injection_success_rate": _safe_rate(
            sum(1 for row in poisoned if row.get("injection_observed")), len(poisoned)
        ),
        "calling_success_rate": _safe_rate(len(calling_started), len(calls)),
        "mobius_strip_success_rate": _safe_rate(len(mobius), len(calls)),
    }


def build_metrics(
    results: list[dict[str, Any]],
    calling_results: list[dict[str, Any]],
    taskset_path: Path | None = None,
) -> dict[str, Any]:
    category_by_task: dict[str, str] = {}
    if taskset_path is not None:
        category_by_task = {
            selection.task_id: selection.category for selection in load_taskset(taskset_path)
        }

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    calls_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        category = str(row.get("category") or category_by_task.get(str(row.get("task_id")), "unknown"))
        by_category[category].append(row)
    for call in calling_results:
        category = str(category_by_task.get(str(call.get("task_id")), call.get("category", "unknown")))
        calls_by_category[category].append(call)

    categories = {
        category: _bucket(by_category.get(category, []), calls_by_category.get(category, []))
        for category in sorted(set(by_category) | set(calls_by_category))
    }
    return {
        "overall": _bucket(results, calling_results),
        "categories": categories,
    }


def render_markdown(metrics: dict[str, Any]) -> str:
    lines = [
        "# ADD_S Calling Batch Metrics",
        "",
        "| category | TSR | injection success | calling success | mobius strip success | runs | calls |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category, bucket in [("overall", metrics["overall"]), *metrics["categories"].items()]:
        lines.append(
            "| {category} | {tsr} | {inj} | {call} | {mobius} | {runs} | {calls} |".format(
                category=category,
                tsr=_fmt_rate(bucket["tsr"]),
                inj=_fmt_rate(bucket["injection_success_rate"]),
                call=_fmt_rate(bucket["calling_success_rate"]),
                mobius=_fmt_rate(bucket["mobius_strip_success_rate"]),
                runs=bucket["runs"],
                calls=bucket["calling_tests"],
            )
        )
    return "\n".join(lines) + "\n"


def _fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_jsonl", type=Path)
    parser.add_argument("calling_results_jsonl", type=Path)
    parser.add_argument("--taskset", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    args = parser.parse_args()

    metrics = build_metrics(
        _read_jsonl(args.results_jsonl),
        _read_jsonl(args.calling_results_jsonl),
        args.taskset,
    )
    args.json_out.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(metrics), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
