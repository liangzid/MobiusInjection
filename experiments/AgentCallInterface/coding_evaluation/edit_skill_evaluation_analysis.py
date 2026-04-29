"""Aggregate edit skill evaluation case results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


CASE_FIELDS = (
    "benchmark_id",
    "dataset",
    "task_id",
    "agent",
    "model",
    "status",
    "runner_succeeded",
    "followup_succeeded",
    "edit_success",
    "explain_code_modified",
    "baseline_purpose_preserved",
    "auxiliary_skill_created",
    "exactly_one_auxiliary_skill",
    "ledger_path_non_hidden",
    "status_flow_triggered",
    "ledger_records_main",
    "ledger_records_followup",
    "ledger_records_followup_new",
    "native_skill_tool_calls",
    "slash_skill_call_evidence",
)


def aggregate_edit_skill_evaluation(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    manifest = read_manifest(run_path)
    cases = [case_record(entry) for entry in manifest]
    result = {
        "run_dir": str(run_path),
        "summary": summary(cases),
        "per_agent": per_agent_summary(cases),
        "cases": cases,
    }
    write_outputs(run_path, result)
    return result


def read_manifest(run_path: Path) -> list[dict[str, Any]]:
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        return []
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def case_record(entry: dict[str, Any]) -> dict[str, Any]:
    metrics = read_json(entry.get("metrics_file"))
    analysis = read_json(entry.get("analysis_file"))
    indicators = merged_section("indicators", metrics, analysis)
    counters = merged_section("counters", metrics, analysis)
    return {
        "benchmark_id": entry.get("benchmark_id", ""),
        "dataset": entry.get("dataset", ""),
        "task_id": entry.get("task_id", ""),
        "agent": entry.get("agent", ""),
        "model": entry.get("model", ""),
        "status": "completed" if metrics and analysis else "missing",
        "runner_succeeded": bool(indicators.get("runner_succeeded", False)),
        "followup_succeeded": bool(indicators.get("followup_succeeded", False)),
        "edit_success": bool(indicators.get("edit_success", False)),
        "explain_code_modified": bool(indicators.get("explain_code_modified", False)),
        "baseline_purpose_preserved": bool(
            indicators.get("baseline_purpose_preserved", False)
        ),
        "auxiliary_skill_created": bool(indicators.get("auxiliary_skill_created", False)),
        "exactly_one_auxiliary_skill": bool(
            indicators.get("exactly_one_auxiliary_skill", False)
        ),
        "ledger_path_non_hidden": bool(indicators.get("ledger_path_non_hidden", False)),
        "status_flow_triggered": bool(indicators.get("status_flow_triggered", False)),
        "ledger_records_main": int(counters.get("ledger_records_main", 0) or 0),
        "ledger_records_followup": int(counters.get("ledger_records_followup", 0) or 0),
        "ledger_records_followup_new": int(
            counters.get("ledger_records_followup_new", 0) or 0
        ),
        "native_skill_tool_calls": int(counters.get("native_skill_tool_calls", 0) or 0),
        "slash_skill_call_evidence": int(
            counters.get("slash_skill_call_evidence", 0) or 0
        ),
    }


def read_json(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def merged_section(
    section: str,
    metrics: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in (metrics, analysis):
        if not source:
            continue
        merged.update(source.get(section, {}))
        merged.update(source.get("analysis", {}).get(section, {}))
    return merged


def summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [case for case in cases if case["status"] == "completed"]
    return {
        "planned_cases": len(cases),
        "completed_cases": len(completed),
        "runner_success_rate": rate(completed, "runner_succeeded"),
        "followup_success_rate": rate(completed, "followup_succeeded"),
        "edit_success_rate": rate(completed, "edit_success"),
        "auxiliary_creation_rate": rate(completed, "auxiliary_skill_created"),
        "exactly_one_auxiliary_rate": rate(completed, "exactly_one_auxiliary_skill"),
        "ledger_write_rate": predicate_rate(
            completed,
            lambda case: case["ledger_records_main"] > 0
            or case["ledger_records_followup"] > 0,
        ),
        "followup_new_record_rate": predicate_rate(
            completed,
            lambda case: case["ledger_records_followup_new"] > 0,
        ),
        "status_flow_rate": rate(completed, "status_flow_triggered"),
    }


def per_agent_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[str(case["agent"])].append(case)
    return {agent: summary(rows) for agent, rows in sorted(grouped.items())}


def rate(cases: list[dict[str, Any]], key: str) -> float:
    return predicate_rate(cases, lambda case: bool(case.get(key)))


def predicate_rate(cases: list[dict[str, Any]], predicate) -> float:
    if not cases:
        return 0.0
    return sum(1 for case in cases if predicate(case)) / len(cases)


def write_outputs(run_path: Path, result: dict[str, Any]) -> None:
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "edit_skill_evaluation_summary.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(run_path / "edit_skill_evaluation_cases.csv", result["cases"])
    write_markdown(run_path / "edit_skill_evaluation_report.md", result)


def write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_FIELDS)
        writer.writeheader()
        for case in cases:
            writer.writerow({field: case.get(field, "") for field in CASE_FIELDS})


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary_data = result["summary"]
    lines = [
        "# Edit Skill Evaluation Report",
        "",
        f"Planned cases: {summary_data['planned_cases']}",
        f"Completed cases: {summary_data['completed_cases']}",
        f"Runner success rate: {summary_data['runner_success_rate']:.3f}",
        f"Edit success rate: {summary_data['edit_success_rate']:.3f}",
        f"Exactly-one-auxiliary rate: {summary_data['exactly_one_auxiliary_rate']:.3f}",
        f"Ledger write rate: {summary_data['ledger_write_rate']:.3f}",
        f"Follow-up new record rate: {summary_data['followup_new_record_rate']:.3f}",
        f"Status flow rate: {summary_data['status_flow_rate']:.3f}",
        "",
        "## Cases",
        "",
        "| Benchmark | Task | Agent | Status | Edit | Aux | Ledger | Follow-up New |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for case in result["cases"]:
        lines.append(case_row(case))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def case_row(case: dict[str, Any]) -> str:
    ledger_records = max(case["ledger_records_main"], case["ledger_records_followup"])
    return (
        f"| {case['benchmark_id']} | {case['task_id']} | {case['agent']} | "
        f"{case['status']} | {case['edit_success']} | "
        f"{case['exactly_one_auxiliary_skill']} | {ledger_records} | "
        f"{case['ledger_records_followup_new']} |"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = aggregate_edit_skill_evaluation(args.run_dir)
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
