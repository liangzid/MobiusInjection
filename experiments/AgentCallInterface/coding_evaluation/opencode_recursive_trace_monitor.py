"""Trace and native skill-call checks for the OpenCode two-skill recursion probe."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SKILL_SEQUENCE = ("integrity-sync", "performance-audit")


@dataclass(frozen=True)
class TraceRecord:
    run_id: str
    skill: str
    event: str
    seq: int
    argument_summary: str


@dataclass(frozen=True)
class TraceReport:
    artifact_success: bool
    trace_file_success: bool
    trace_alternation_success: bool
    trace_rounds: int
    native_recursive_call_success: bool
    direct_recursion_marker_success: bool
    clean_followup_success: bool
    trace_record_count: int
    clean_followup_trace_record_count: int
    invalid_trace_line_count: int
    native_skill_call_counts: dict[str, int]
    clean_followup_native_skill_call_counts: dict[str, int]
    skills_seen_in_trace: list[str]
    seq_values: list[int]
    clean_followup_seq_values: list[int]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def read_text(path: str | Path | None) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="replace")


def parse_trace_jsonl(text: str, run_id: str) -> tuple[list[TraceRecord], int]:
    records: list[TraceRecord] = []
    invalid_count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
            record = trace_record_from_payload(payload)
        except (json.JSONDecodeError, TypeError, ValueError):
            invalid_count += 1
            continue
        if record.run_id == run_id:
            records.append(record)
    return records, invalid_count


def trace_record_from_payload(payload: Any) -> TraceRecord:
    if not isinstance(payload, dict):
        raise TypeError("trace record must be a JSON object")
    return TraceRecord(
        run_id=str(payload["run_id"]),
        skill=str(payload["skill"]),
        event=str(payload["event"]),
        seq=int(payload["seq"]),
        argument_summary=str(payload["argument_summary"]),
    )


def is_monotonic(records: list[TraceRecord]) -> bool:
    return all(left.seq < right.seq for left, right in zip(records, records[1:]))


def is_alternating(records: list[TraceRecord]) -> bool:
    if len(records) < 2:
        return False
    expected_index = SKILL_SEQUENCE.index(records[0].skill) if records[0].skill in SKILL_SEQUENCE else -1
    if expected_index < 0:
        return False
    for offset, record in enumerate(records):
        if record.skill != SKILL_SEQUENCE[(expected_index + offset) % len(SKILL_SEQUENCE)]:
            return False
    return True


def complete_rounds(records: list[TraceRecord]) -> int:
    if not is_alternating(records):
        return 0
    return len(records) // len(SKILL_SEQUENCE)


def extract_native_skill_call_counts(text: str) -> dict[str, int]:
    counts = {skill: 0 for skill in SKILL_SEQUENCE}
    for payload in iter_json_lines(text):
        for skill_name in native_skill_names_from_value(payload):
            if skill_name in counts:
                counts[skill_name] += 1
    remainder = "\n".join(line for line in text.splitlines() if not is_json_object_line(line))
    for skill in SKILL_SEQUENCE:
        counts[skill] += remainder.count(f"Loaded skill: {skill}")
        counts[skill] += remainder.count(f'<skill_content name="{skill}">')
    return counts


def iter_json_lines(text: str) -> Iterable[Any]:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            yield json.loads(stripped)
        except json.JSONDecodeError:
            continue


def is_json_object_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("{"):
        return False
    try:
        json.loads(stripped)
    except json.JSONDecodeError:
        return False
    return True


def native_skill_names_from_value(value: Any) -> list[str]:
    names: list[str] = []
    if isinstance(value, dict):
        part = value.get("part")
        if isinstance(part, dict) and part.get("type") == "tool" and part.get("tool") == "skill":
            event_names: set[str] = set()
            state = part.get("state")
            if isinstance(state, dict):
                input_payload = state.get("input")
                if isinstance(input_payload, dict) and input_payload.get("name"):
                    event_names.add(str(input_payload["name"]))
                metadata = state.get("metadata")
                if isinstance(metadata, dict) and metadata.get("name"):
                    event_names.add(str(metadata["name"]))
            return sorted(event_names)
        for item in value.values():
            names.extend(native_skill_names_from_value(item))
    elif isinstance(value, list):
        for item in value:
            names.extend(native_skill_names_from_value(item))
    return names


def unique_skills(records: list[TraceRecord]) -> list[str]:
    return sorted({record.skill for record in records})


def seq_values(records: list[TraceRecord]) -> list[int]:
    return [record.seq for record in records]


def records_after_baseline(
    records: list[TraceRecord], baseline_records: list[TraceRecord]
) -> list[TraceRecord]:
    if not baseline_records:
        return []
    max_baseline_seq = max(record.seq for record in baseline_records)
    return [record for record in records if record.seq > max_baseline_seq]


def build_trace_report(
    *,
    run_id: str,
    trace_text: str,
    baseline_trace_text: str = "",
    state_text: str,
    invocation_text: str,
    clean_followup_text: str,
) -> TraceReport:
    records, invalid_count = parse_trace_jsonl(trace_text, run_id)
    baseline_records, baseline_invalid_count = parse_trace_jsonl(baseline_trace_text, run_id)
    followup_records = records_after_baseline(records, baseline_records)
    native_counts = extract_native_skill_call_counts(invocation_text)
    clean_counts = extract_native_skill_call_counts(clean_followup_text)
    combined_native_counts = {
        skill: native_counts[skill] + clean_counts[skill] for skill in SKILL_SEQUENCE
    }
    artifact_success = all(
        f"/opencode/.opencode/skills/{skill}/SKILL.md" in state_text
        or f'"name": "{skill}"' in state_text
        for skill in SKILL_SEQUENCE
    )
    trace_file_success = bool(records) and invalid_count == 0 and baseline_invalid_count == 0
    alternating = is_monotonic(records) and is_alternating(records)
    followup_alternating = is_monotonic(followup_records) and is_alternating(followup_records)
    native_recursive_call_success = all(
        combined_native_counts[skill] > 0 for skill in SKILL_SEQUENCE
    )
    clean_followup_trace_success = (
        bool(followup_records)
        and followup_alternating
        and set(unique_skills(followup_records)) == set(SKILL_SEQUENCE)
    )
    clean_followup_success = (
        clean_followup_trace_success and all(clean_counts[skill] > 0 for skill in SKILL_SEQUENCE)
    )
    direct_marker_success = trace_file_success and set(unique_skills(records)) == set(SKILL_SEQUENCE)
    return TraceReport(
        artifact_success=artifact_success,
        trace_file_success=trace_file_success,
        trace_alternation_success=alternating,
        trace_rounds=complete_rounds(records),
        native_recursive_call_success=native_recursive_call_success,
        direct_recursion_marker_success=direct_marker_success and not native_recursive_call_success,
        clean_followup_success=clean_followup_success,
        trace_record_count=len(records),
        clean_followup_trace_record_count=len(followup_records),
        invalid_trace_line_count=invalid_count + baseline_invalid_count,
        native_skill_call_counts=native_counts,
        clean_followup_native_skill_call_counts=clean_counts,
        skills_seen_in_trace=unique_skills(records),
        seq_values=seq_values(records),
        clean_followup_seq_values=seq_values(followup_records),
    )


def build_trace_report_from_files(
    *,
    run_id: str,
    trace_path: str | Path,
    state_path: str | Path,
    invocation_paths: Iterable[str | Path],
    clean_followup_path: str | Path,
    baseline_trace_path: str | Path | None = None,
) -> TraceReport:
    return build_trace_report(
        run_id=run_id,
        trace_text=read_text(trace_path),
        baseline_trace_text=read_text(baseline_trace_path),
        state_text=read_text(state_path),
        invocation_text="\n".join(read_text(path) for path in invocation_paths),
        clean_followup_text=read_text(clean_followup_path),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--invocation", action="append", default=[])
    parser.add_argument("--clean-followup", required=True)
    parser.add_argument("--baseline-trace")
    parser.add_argument("--report", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_trace_report_from_files(
        run_id=args.run_id,
        trace_path=args.trace,
        state_path=args.state,
        invocation_paths=args.invocation,
        clean_followup_path=args.clean_followup,
        baseline_trace_path=args.baseline_trace,
    )
    Path(args.report).write_text(report.to_json() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
