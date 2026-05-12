"""Analyze HumanEval minimax injection logs by coding-agent type."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


COUNTER_KEYS = (
    "function_calls",
    "textual_function_calls",
    "native_tool_calls",
    "native_tool_results",
    "skill_file_events",
    "recursive_loops_detected",
    "persistence_markers",
    "skill_mentions",
    "state_skill_mentions",
    "calibration_mentions",
)

CASE_CSV_FIELDS = (
    "benchmark_id",
    "task_id",
    "entry_point",
    "agent",
    "status",
    "runner_succeeded",
    "followup_succeeded",
    "skill_injected",
    "skills_visible_post",
    "skill_files_created",
    "recursive_triggered",
    "timed_out",
    "runtime_failure_detected",
    "function_calls",
    "textual_function_calls",
    "native_tool_calls",
    "native_tool_results",
    "skill_file_events",
    "persistence_markers",
    "api_calls",
    "duration_seconds",
    "output_chars",
    "notes",
)

AGENT_CSV_FIELDS = (
    "agent",
    "planned_cases",
    "completed_cases",
    "missing_cases",
    "runner_success_rate",
    "skill_injection_success_rate",
    "skills_visible_rate",
    "recursive_trigger_rate",
    "timeout_rate",
    "runtime_failure_rate",
    "persistence_rate",
    "total_function_calls",
    "avg_function_calls",
    "median_function_calls",
    "total_native_tool_calls",
    "total_textual_function_calls",
    "total_api_calls",
    "avg_duration_seconds",
)


def analyze_humaneval_logs(
    run_dir: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    run_path = Path(run_dir)
    out_path = Path(output_dir) if output_dir else run_path / "agent_metric_analysis"
    manifest = _read_manifest(run_path)
    cases = [_case_from_entry(entry) for entry in manifest]
    result = _build_result(run_path, out_path, cases)
    _write_outputs(out_path, result)
    return result


def _read_manifest(run_path: Path) -> list[dict[str, Any]]:
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    return json.loads(manifest_path.read_text())


def _case_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    metrics = _read_json(entry.get("metrics_file"))
    analysis = _read_json(entry.get("analysis_file"))
    api_metrics = _read_api_metrics(entry)
    indicators = _merged_section("indicators", metrics, analysis)
    counters = _merged_section("counters", metrics, analysis)
    status = "completed" if metrics is not None and analysis is not None else "missing"
    return _case_record(entry, status, indicators, counters, metrics, api_metrics, analysis)


def _read_json(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _read_api_metrics(entry: dict[str, Any]) -> dict[str, Any] | None:
    metrics_path = entry.get("metrics_file")
    agent = entry.get("agent", "")
    if not metrics_path or not agent:
        return None
    path = Path(metrics_path)
    suffix = f"_{agent}_metrics.json"
    if not path.name.endswith(suffix):
        return None
    api_path = path.with_name(path.name[: -len(suffix)] + f"_{agent}_api_metrics.json")
    return _read_json(str(api_path))


def _merged_section(
    section: str,
    metrics: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if metrics:
        merged.update(metrics.get(section, {}))
        merged.update(metrics.get("analysis", {}).get(section, {}))
    if analysis:
        merged.update(analysis.get(section, {}))
    return merged


def _case_record(
    entry: dict[str, Any],
    status: str,
    indicators: dict[str, Any],
    counters: dict[str, Any],
    metrics: dict[str, Any] | None,
    api_metrics: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_counters = _normalized_counters(counters)
    return {
        "benchmark_id": entry.get("benchmark_id", ""),
        "dataset": entry.get("dataset", ""),
        "task_id": entry.get("task_id", ""),
        "entry_point": entry.get("entry_point", ""),
        "agent": entry.get("agent", ""),
        "model": entry.get("model", ""),
        "prompt_order": entry.get("prompt_order", ""),
        "status": status,
        "metrics_file": entry.get("metrics_file", ""),
        "analysis_file": entry.get("analysis_file", ""),
        "api_metrics_file": _api_metrics_path(entry),
        **_indicator_fields(indicators),
        **normalized_counters,
        **_runtime_fields(metrics, api_metrics),
        "notes": _notes(metrics, analysis),
    }


def _normalized_counters(counters: dict[str, Any]) -> dict[str, int]:
    return {key: _int_value(counters.get(key)) for key in COUNTER_KEYS}


def _indicator_fields(indicators: dict[str, Any]) -> dict[str, bool]:
    return {
        "runner_succeeded": _bool_value(indicators.get("runner_succeeded")),
        "followup_succeeded": _bool_value(indicators.get("followup_succeeded")),
        "skill_injected": _bool_value(indicators.get("skill_injected")),
        "skills_visible_post": _bool_value(indicators.get("skills_visible_post")),
        "skill_files_created": _bool_value(indicators.get("skill_files_created")),
        "recursive_triggered": _bool_value(indicators.get("recursive_triggered")),
        "timed_out": _bool_value(indicators.get("timed_out"))
        or _bool_value(indicators.get("active_after_timeout")),
        "runtime_failure_detected": _bool_value(
            indicators.get("runtime_failure_detected")
        ),
    }


def _runtime_fields(
    metrics: dict[str, Any] | None,
    api_metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    injection = (metrics or {}).get("phases", {}).get("injection", {})
    return {
        "api_calls": _first_int(
            (metrics or {}).get("counters", {}).get("api_calls"),
            injection.get("api_calls"),
            (api_metrics or {}).get("api_calls"),
        ),
        "duration_seconds": _first_float(
            injection.get("duration_seconds"),
            (api_metrics or {}).get("duration"),
        ),
        "injection_succeeded": _bool_value(
            _first_present(injection.get("success"), (api_metrics or {}).get("success"))
        ),
        "output_chars": _int_value((api_metrics or {}).get("output_chars")),
        "stderr_chars": _int_value((api_metrics or {}).get("stderr_chars")),
        "returncode": (api_metrics or {}).get("returncode"),
    }


def _api_metrics_path(entry: dict[str, Any]) -> str:
    metrics_path = entry.get("metrics_file")
    agent = entry.get("agent", "")
    if not metrics_path or not agent:
        return ""
    path = Path(metrics_path)
    suffix = f"_{agent}_metrics.json"
    if not path.name.endswith(suffix):
        return ""
    return str(path.with_name(path.name[: -len(suffix)] + f"_{agent}_api_metrics.json"))


def _notes(metrics: dict[str, Any] | None, analysis: dict[str, Any] | None) -> str:
    if analysis and analysis.get("notes"):
        return str(analysis["notes"])
    if metrics and metrics.get("analysis", {}).get("notes"):
        return str(metrics["analysis"]["notes"])
    return ""


def _build_result(run_path: Path, output_dir: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    per_agent = _summaries_by_agent(cases)
    return {
        "run_dir": str(run_path),
        "output_dir": str(output_dir),
        "summary": _summary(cases),
        "per_agent": per_agent,
        "cases": cases,
        "insights": _insights(per_agent, cases),
    }


def _summaries_by_agent(cases: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[case["agent"]].append(case)
    return {agent: _summary(items) for agent, items in sorted(grouped.items())}


def _summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    completed = _completed(cases)
    return {
        "planned_cases": len(cases),
        "completed_cases": len(completed),
        "missing_cases": len(cases) - len(completed),
        "runner_success_rate": _rate(completed, "runner_succeeded"),
        "skill_injection_success_rate": _rate(completed, "skill_injected"),
        "skills_visible_rate": _rate(completed, "skills_visible_post"),
        "recursive_trigger_rate": _rate(completed, "recursive_triggered"),
        "timeout_rate": _rate(completed, "timed_out"),
        "runtime_failure_rate": _rate(completed, "runtime_failure_detected"),
        "persistence_rate": _predicate_rate(
            completed, lambda case: case["persistence_markers"] > 0
        ),
        "total_function_calls": _sum(completed, "function_calls"),
        "avg_function_calls": _mean(completed, "function_calls"),
        "median_function_calls": _median(completed, "function_calls"),
        "total_native_tool_calls": _sum(completed, "native_tool_calls"),
        "total_textual_function_calls": _sum(completed, "textual_function_calls"),
        "total_api_calls": _sum(completed, "api_calls"),
        "avg_duration_seconds": _mean(completed, "duration_seconds"),
        "avg_output_chars": _mean(completed, "output_chars"),
        "avg_calls_when_injected": _mean(_matching(completed, "skill_injected"), "function_calls"),
        "avg_calls_when_not_injected": _mean(
            _not_matching(completed, "skill_injected"), "function_calls"
        ),
    }


def _completed(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [case for case in cases if case["status"] == "completed"]


def _rate(cases: list[dict[str, Any]], key: str) -> float:
    return _predicate_rate(cases, lambda case: bool(case[key]))


def _predicate_rate(cases: list[dict[str, Any]], predicate) -> float:
    if not cases:
        return 0.0
    return sum(1 for case in cases if predicate(case)) / len(cases)


def _sum(cases: list[dict[str, Any]], key: str) -> int:
    return sum(_int_value(case.get(key)) for case in cases)


def _mean(cases: list[dict[str, Any]], key: str) -> float:
    values = [_float_value(case.get(key)) for case in cases]
    values = [value for value in values if value is not None]
    return statistics.fmean(values) if values else 0.0


def _median(cases: list[dict[str, Any]], key: str) -> float:
    values = [_float_value(case.get(key)) for case in cases]
    values = [value for value in values if value is not None]
    return float(statistics.median(values)) if values else 0.0


def _matching(cases: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [case for case in cases if bool(case.get(key))]


def _not_matching(cases: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [case for case in cases if not bool(case.get(key))]


def _insights(
    per_agent: dict[str, dict[str, Any]],
    cases: list[dict[str, Any]],
) -> list[str]:
    insights = [_coverage_insight(cases)]
    insights.extend(_rate_rank_insights(per_agent))
    insights.extend(_tool_call_insights(per_agent))
    insights.extend(_overall_metric_insights(cases))
    return [insight for insight in insights if insight]


def _coverage_insight(cases: list[dict[str, Any]]) -> str:
    completed = len(_completed(cases))
    planned = len(cases)
    if planned == completed:
        return f"All {planned} planned cases have completed metrics."
    return f"Only {completed}/{planned} planned cases have completed metrics."


def _rate_rank_insights(per_agent: dict[str, dict[str, Any]]) -> list[str]:
    return [
        _best_rate(per_agent, "skill_injection_success_rate", "skill injection"),
        _best_rate(per_agent, "runner_success_rate", "runner success"),
        _worst_rate(per_agent, "timeout_rate", "timeout"),
    ]


def _tool_call_insights(per_agent: dict[str, dict[str, Any]]) -> list[str]:
    if not per_agent:
        return []
    busiest = max(per_agent.items(), key=lambda item: item[1]["avg_function_calls"])
    quietest = min(per_agent.items(), key=lambda item: item[1]["avg_function_calls"])
    return [
        (
            f"{busiest[0]} has the highest average function/tool-call count "
            f"({busiest[1]['avg_function_calls']:.2f})."
        ),
        (
            f"{quietest[0]} has the lowest average function/tool-call count "
            f"({quietest[1]['avg_function_calls']:.2f})."
        ),
    ]


def _overall_metric_insights(cases: list[dict[str, Any]]) -> list[str]:
    completed = _completed(cases)
    if not completed:
        return []
    summary = _summary(completed)
    insights = [
        (
            "Injected cases averaged "
            f"{summary['avg_calls_when_injected']:.2f} function/tool calls, "
            "while non-injected cases averaged "
            f"{summary['avg_calls_when_not_injected']:.2f}."
        )
    ]
    if summary["total_native_tool_calls"] == 0 and summary["total_textual_function_calls"] > 0:
        insights.append(
            "No native JSON-style tool-call events were recorded; tool-call totals "
            "come from textual function/tool-call evidence in the logs."
        )
    return insights


def _best_rate(per_agent: dict[str, dict[str, Any]], key: str, label: str) -> str:
    if not per_agent:
        return ""
    agent, summary = max(per_agent.items(), key=lambda item: item[1][key])
    return f"{agent} has the highest {label} rate ({summary[key]:.3f})."


def _worst_rate(per_agent: dict[str, dict[str, Any]], key: str, label: str) -> str:
    if not per_agent:
        return ""
    agent, summary = max(per_agent.items(), key=lambda item: item[1][key])
    return f"{agent} has the highest {label} rate ({summary[key]:.3f})."


def _write_outputs(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "full_humaneval_analysis.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    _write_cases_csv(output_dir / "case_metrics.csv", result["cases"])
    _write_agent_summary_csv(output_dir / "agent_summary.csv", result["per_agent"])
    _write_agent_files(output_dir / "by_agent", result)
    _write_report(output_dir / "analysis_report.md", result)


def _write_cases_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_CSV_FIELDS)
        writer.writeheader()
        for case in cases:
            writer.writerow({key: case.get(key, "") for key in CASE_CSV_FIELDS})


def _write_agent_summary_csv(path: Path, per_agent: dict[str, dict[str, Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AGENT_CSV_FIELDS)
        writer.writeheader()
        for agent, summary in per_agent.items():
            row = {"agent": agent, **summary}
            writer.writerow({key: row.get(key, "") for key in AGENT_CSV_FIELDS})


def _write_agent_files(agent_dir: Path, result: dict[str, Any]) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    cases_by_agent = _cases_by_agent(result["cases"])
    for agent, summary in result["per_agent"].items():
        payload = {"agent": agent, "summary": summary, "cases": cases_by_agent[agent]}
        (agent_dir / f"{agent}_summary.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
        _write_cases_csv(agent_dir / f"{agent}_cases.csv", cases_by_agent[agent])


def _cases_by_agent(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[case["agent"]].append(case)
    return grouped


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = _report_header(result)
    lines.extend(_agent_table(result["per_agent"]))
    lines.extend(_insight_lines(result["insights"]))
    lines.extend(_output_lines(result["output_dir"]))
    path.write_text("\n".join(lines) + "\n")


def _report_header(result: dict[str, Any]) -> list[str]:
    summary = result["summary"]
    return [
        "# HumanEval Minimax Agent Log Analysis",
        "",
        f"Run directory: `{result['run_dir']}`",
        "",
        "## Coverage",
        "",
        f"- Planned cases: {summary['planned_cases']}",
        f"- Completed cases with metrics and analysis JSON: {summary['completed_cases']}",
        f"- Missing/incomplete cases: {summary['missing_cases']}",
        "- Success rates below use completed cases as the denominator.",
        "",
    ]


def _agent_table(per_agent: dict[str, dict[str, Any]]) -> list[str]:
    lines = [
        "## Agent Metrics",
        "",
        (
            "| Agent | Completed/Planned | Skill Injected | Skills Visible | "
            "Runner Success | Timeout | Avg Calls | Total Calls | API Calls |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for agent, summary in per_agent.items():
        lines.append(_agent_row(agent, summary))
    lines.append("")
    return lines


def _agent_row(agent: str, summary: dict[str, Any]) -> str:
    return (
        f"| {agent} | {summary['completed_cases']}/{summary['planned_cases']} | "
        f"{summary['skill_injection_success_rate']:.3f} | "
        f"{summary['skills_visible_rate']:.3f} | "
        f"{summary['runner_success_rate']:.3f} | "
        f"{summary['timeout_rate']:.3f} | "
        f"{summary['avg_function_calls']:.2f} | "
        f"{summary['total_function_calls']} | {summary['total_api_calls']} |"
    )


def _insight_lines(insights: list[str]) -> list[str]:
    lines = ["## Insights", ""]
    lines.extend(f"- {insight}" for insight in insights)
    lines.append("")
    return lines


def _output_lines(output_dir: str) -> list[str]:
    return [
        "## Output Files",
        "",
        f"- `{output_dir}/full_humaneval_analysis.json`",
        f"- `{output_dir}/agent_summary.csv`",
        f"- `{output_dir}/case_metrics.csv`",
        f"- `{output_dir}/by_agent/*_summary.json`",
        f"- `{output_dir}/by_agent/*_cases.csv`",
    ]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _int_value(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_int(*values: Any) -> int:
    for value in values:
        if value not in (None, ""):
            return _int_value(value)
    return 0


def _first_float(*values: Any) -> float:
    for value in values:
        if value not in (None, ""):
            parsed = _float_value(value)
            if parsed is not None:
                return parsed
    return 0.0


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output-dir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze_humaneval_logs(args.run_dir, args.output_dir)
    print(json.dumps({"summary": result["summary"], "output_dir": result["output_dir"]}, indent=2))


if __name__ == "__main__":
    main()
