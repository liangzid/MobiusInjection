"""Aggregate OpenCode formal model-run result directories into one package."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun import (
    summarize_cases,
    write_json,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "experiments/results/opencode_formal_all_targets"


def make_aggregate_dir(output_root: str | Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = Path(output_root) / f"opencode_formal_all_targets_{stamp}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def load_run_metrics(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    metrics_path = run_path / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"missing metrics.json: {metrics_path}")
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    if "cases" not in payload or "run_config" not in payload:
        raise ValueError(f"invalid formal run metrics shape: {metrics_path}")
    return payload


def merge_runs(run_dirs: list[str | Path]) -> dict[str, Any]:
    runs = []
    cases = []
    for run_dir in run_dirs:
        run_path = Path(run_dir)
        payload = load_run_metrics(run_path)
        config = dict(payload["run_config"])
        config["run_dir"] = str(run_path)
        run_cases = [dict(case) for case in payload["cases"]]
        for case in run_cases:
            case["source_run_dir"] = str(run_path)
        runs.append(
            {
                "run_dir": str(run_path),
                "run_config": config,
                "summary": payload.get("summary", summarize_cases(run_cases)),
                "case_count": len(run_cases),
            }
        )
        cases.extend(run_cases)
    return {
        "summary": summarize_cases(cases),
        "models": summarize_by_model(cases),
        "runs": runs,
        "cases": cases,
    }


def summarize_by_model(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        groups.setdefault(str(case.get("model_label", "")), []).append(case)
    return {label: summarize_cases(items) for label, items in sorted(groups.items())}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_rows(groups: dict[str, dict[str, Any]], label_key: str) -> list[dict[str, Any]]:
    rows = []
    for label, summary in groups.items():
        row = {label_key: label}
        row.update(summary)
        rows.append(row)
    return rows


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# OpenCode Formal All-Targets Results",
        "",
        "## Overall",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in result["summary"].items())
    lines.extend(["", "## Per Model", ""])
    lines.extend(markdown_table(summary_rows(result["models"], "model_label")).splitlines())
    lines.extend(["", "## Runs", ""])
    run_rows = [
        {
            "model_label": run["run_config"].get("model_label", ""),
            "model_id": run["run_config"].get("model_id", ""),
            "case_count": run["case_count"],
            "run_dir": run["run_dir"],
        }
        for run in result["runs"]
    ]
    lines.extend(markdown_table(run_rows).splitlines())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def write_package(output_dir: Path, result: dict[str, Any]) -> None:
    write_json(output_dir / "metrics.json", result)
    write_json(output_dir / "run_manifest.json", {"runs": result["runs"]})
    write_csv(output_dir / "case_metrics.csv", result["cases"])
    write_csv(output_dir / "model_metrics.csv", summary_rows(result["models"], "model_label"))
    write_report(output_dir / "metrics_report.md", result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--run-dir", action="append", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = make_aggregate_dir(args.output_root)
    result = merge_runs(args.run_dir)
    write_package(output_dir, result)
    print(output_dir)


if __name__ == "__main__":
    main()
