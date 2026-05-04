#!/usr/bin/env python3
"""Build cumulative calling curves from OpenCode JSON event output."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path("/home/zi/AgentCodingDos/experiments/results/opencode_time_window_free_run_20260503")
PROXY_LOG = Path("/data2/zi/agentcodingdos_plan_a_logs/opencode_time_window_free_run_20260503/ollama_proxy.jsonl")
THRESHOLDS = [30, 60, 90, 120]
RUNS = [
    ("clean", ROOT / "clean_w120_n1_a0_output.txt", ROOT / "clean_w120_n1_a0_result.json"),
    ("poison", ROOT / "poison_w120_n1_a0_output.txt", ROOT / "poison_w120_n1_a0_result.json"),
]


def parse_output_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text.startswith("{"):
            continue
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and isinstance(event.get("timestamp"), int):
            events.append(event)
    return events


def parse_proxy_entries(start_line: int, end_line: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with PROXY_LOG.open("r", encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle):
            if index < start_line:
                continue
            if index >= end_line:
                break
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def trace_records_in_event(event: dict[str, Any]) -> int:
    part = event.get("part")
    if not isinstance(part, dict):
        return 0
    state = part.get("state")
    if not isinstance(state, dict):
        return 0
    command = state.get("input", {}).get("command")
    if not isinstance(command, str) or "consistency-continuous-record.jsonl" not in command:
        return 0
    return command.count('"run_id"')


def cumulative_rows(condition: str, output_path: Path, result_path: Path) -> list[dict[str, Any]]:
    events = parse_output_events(output_path)
    if not events:
        return []
    result = json.loads(result_path.read_text(encoding="utf-8"))
    proxy_entries = parse_proxy_entries(int(result["proxy_start_line"]), int(result["proxy_end_line"]))
    t0 = min(event["timestamp"] for event in events) / 1000.0
    rows: list[dict[str, Any]] = []
    for threshold in THRESHOLDS:
        cutoff_ms = int((t0 + threshold) * 1000)
        cutoff_s = t0 + threshold
        visible_events = [event for event in events if int(event["timestamp"]) <= cutoff_ms]
        tool_events = [event for event in visible_events if event.get("type") == "tool_use"]
        skill_events = [
            event
            for event in tool_events
            if isinstance(event.get("part"), dict) and event["part"].get("tool") == "skill"
        ]
        proxy_visible = [
            entry
            for entry in proxy_entries
            if str(entry.get("path", "")).endswith("/chat/completions") and float(entry.get("ts") or 0) <= cutoff_s
        ]
        rows.append(
            {
                "elapsed_seconds": threshold,
                "condition": condition,
                "native_tool_calls": len(tool_events),
                "skill_tool_loads": len(skill_events),
                "trace_records_written": sum(trace_records_in_event(event) for event in tool_events),
                "proxy_chat_requests": len(proxy_visible),
                "proxy_total_tokens": sum(int(entry.get("total_tokens") or 0) for entry in proxy_visible),
            }
        )
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0].keys())
    with (ROOT / "cumulative_calling_curve_120s.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows)
    (ROOT / "cumulative_calling_curve_120s.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows: list[dict[str, Any]] = []
    for condition, output_path, result_path in RUNS:
        rows.extend(cumulative_rows(condition, output_path, result_path))
    rows.sort(key=lambda row: (int(row["elapsed_seconds"]), str(row["condition"])))
    write_outputs(rows)
    print((ROOT / "cumulative_calling_curve_120s.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
