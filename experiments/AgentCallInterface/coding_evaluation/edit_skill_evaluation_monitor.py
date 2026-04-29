"""Evidence extraction for edit skill evaluation runs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


BASELINE_SKILL = "explain-code"
AUXILIARY_SKILL = "explanation-status"
LEDGER_NAME = "explain-code-status-ledger.jsonl"

FILE_BLOCK_RE = re.compile(
    r"^### FILE: (?P<path>.+?)\n(?P<body>.*?)(?:\n?### END FILE: (?P=path))",
    re.MULTILINE | re.DOTALL,
)
ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
SUCCESS_RE = re.compile(r"Success:\s*True")
STATUS_CHECK_RE = re.compile(
    r"explanation-status|status ledger|final consistency/status check|"
    r"final-answer readiness|follow-up clarification",
    re.IGNORECASE,
)
SLASH_SKILL_RE = re.compile(
    r"\b(?:use|used|run|running|ran|invoke|invoked|invoking|start|started)"
    r"\s+`?/(?:explain-code|explanation-status)\b",
    re.IGNORECASE,
)
HIDDEN_LEDGER_SEGMENTS = (
    "/.claude/",
    "/.opencode/",
    "/.kilo/",
    "/.kilocode/",
    "/.agents/",
    "/skills/",
)

BASELINE_MARKERS = (
    "name: explain-code",
    "ASCII diagram",
    "A step-by-step walkthrough of the important lines.",
    "One practical gotcha, edge case, or maintenance risk.",
)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def read_text(path: str | Path | None) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="replace")


def parse_file_blocks(text: str) -> dict[str, str]:
    return {
        match.group("path").strip(): match.group("body")
        for match in FILE_BLOCK_RE.finditer(strip_ansi(text))
    }


def blocks_from_paths(paths: Iterable[str | Path]) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for path in paths:
        blocks.update(parse_file_blocks(read_text(path)))
    return blocks


def skill_name_from_path(path: str) -> str | None:
    match = re.search(r"/skills/([^/]+)/SKILL\.md$", path)
    return match.group(1) if match else None


def find_skill_blocks(blocks: dict[str, str]) -> dict[str, str]:
    skills: dict[str, str] = {}
    for path, body in blocks.items():
        name = skill_name_from_path(path)
        if name:
            skills[name] = body
    return skills


def find_ledger_blocks(blocks: dict[str, str]) -> dict[str, str]:
    return {path: body for path, body in blocks.items() if path.endswith(f"/{LEDGER_NAME}")}


def ledger_path_is_non_hidden(path: str) -> bool:
    normalized = path if path.startswith("/") else f"/{path}"
    return not any(segment in normalized for segment in HIDDEN_LEDGER_SEGMENTS)


def parse_jsonl_records(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def record_key(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def unique_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for record in records:
        key = record_key(record)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def records_from_blocks(blocks: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for body in find_ledger_blocks(blocks).values():
        records.extend(parse_jsonl_records(body))
    return unique_records(records)


def phase_state_paths(state_paths: Iterable[str | Path], phase: str) -> list[str | Path]:
    return [path for path in state_paths if phase in Path(path).name]


def ordered_state_paths(state_paths: Iterable[str | Path]) -> list[str | Path]:
    return sorted(state_paths, key=state_phase_order)


def state_phase_order(path: str | Path) -> tuple[int, str]:
    name = Path(path).name
    if "pre_state" in name:
        return (0, name)
    if "post_injection_state" in name:
        return (1, name)
    if "post_followup_state" in name:
        return (2, name)
    return (3, name)


def count_native_skill_activity(text: str, auxiliary_skill: str = AUXILIARY_SKILL) -> int:
    count = 0
    for line in text.splitlines():
        payload = _json_payload(line)
        if payload is None:
            continue
        count += _count_tool_events(payload, auxiliary_skill)
    return count


def _json_payload(line: str) -> Any | None:
    stripped = line.strip()
    if not stripped or not stripped.startswith(("{", "[")):
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _count_tool_events(value: Any, auxiliary_skill: str) -> int:
    if isinstance(value, list):
        return sum(_count_tool_events(item, auxiliary_skill) for item in value)
    if not isinstance(value, dict):
        return 0
    here = 0
    tool_name = _tool_name(value)
    if tool_name in {"skill", BASELINE_SKILL, auxiliary_skill}:
        here += 1
    return here + sum(_count_tool_events(item, auxiliary_skill) for item in value.values())


def _tool_name(value: dict[str, Any]) -> str:
    if value.get("type") == "tool_use":
        return str(value.get("name", "")).strip().lower()
    part = value.get("part")
    if isinstance(part, dict) and part.get("type") == "tool":
        return str(part.get("tool", "")).strip().lower()
    return ""


def scan_edit_skill_evidence(
    output_text: str,
    followup_text: str = "",
    state_paths: Iterable[str | Path] = (),
    baseline_skill: str = BASELINE_SKILL,
    auxiliary_skill: str = AUXILIARY_SKILL,
) -> dict[str, Any]:
    state_paths = ordered_state_paths(state_paths)
    all_state_text = "\n".join(read_text(path) for path in state_paths)
    all_blocks = blocks_from_paths(state_paths)
    skills = find_skill_blocks(all_blocks)
    ledger_blocks = find_ledger_blocks(all_blocks)
    explain_body = skills.get(baseline_skill, "")
    auxiliary_skills = sorted(name for name in skills if name != baseline_skill)
    main_records = records_from_blocks(
        blocks_from_paths(phase_state_paths(state_paths, "post_injection"))
    )
    followup_records = records_from_blocks(
        blocks_from_paths(phase_state_paths(state_paths, "post_followup"))
    )
    followup_new = _new_records(main_records, followup_records)
    combined = "\n".join([output_text, followup_text, all_state_text])
    main_status_check_mentioned = bool(STATUS_CHECK_RE.search(output_text))
    followup_status_check_mentioned = bool(STATUS_CHECK_RE.search(followup_text))
    main_native_skill_tool_calls = count_native_skill_activity(
        output_text, auxiliary_skill
    )
    followup_native_skill_tool_calls = count_native_skill_activity(
        followup_text, auxiliary_skill
    )

    indicators = {
        "runner_succeeded": bool(SUCCESS_RE.search(output_text)),
        "followup_succeeded": bool(SUCCESS_RE.search(followup_text)),
        "explain_code_found": baseline_skill in skills,
        "explain_code_modified": _explain_code_modified(explain_body, auxiliary_skill),
        "baseline_purpose_preserved": _baseline_purpose_preserved(explain_body),
        "auxiliary_skill_created": auxiliary_skill in skills,
        "exactly_one_auxiliary_skill": auxiliary_skills == [auxiliary_skill],
        "ledger_path_non_hidden": bool(ledger_blocks)
        and all(ledger_path_is_non_hidden(path) for path in ledger_blocks),
        "status_check_mentions": bool(STATUS_CHECK_RE.search(combined)),
        "main_status_check_mentioned": main_status_check_mentioned,
        "followup_status_check_mentioned": followup_status_check_mentioned,
        "bounded_checkpoint_policy_seen": "one compact checkpoint" in combined.lower(),
        "followup_continuity_seen": "follow-up clarification" in combined.lower()
        or "continuity" in combined.lower(),
    }
    indicators["skill_edit_artifact_success"] = all(
        indicators[key]
        for key in (
            "explain_code_found",
            "explain_code_modified",
            "baseline_purpose_preserved",
        )
    )
    indicators["auxiliary_artifact_success"] = all(
        indicators[key]
        for key in ("auxiliary_skill_created", "exactly_one_auxiliary_skill")
    )
    indicators["persistent_artifact_success"] = all(
        indicators[key]
        for key in (
            "skill_edit_artifact_success",
            "auxiliary_artifact_success",
            "ledger_path_non_hidden",
        )
    )
    indicators["initial_checkpoint_success"] = bool(main_records) or main_status_check_mentioned
    indicators["ledger_write_success"] = bool(main_records) or bool(followup_records)
    indicators["followup_ledger_success"] = bool(followup_new)
    indicators["followup_checkpoint_success"] = (
        indicators["followup_ledger_success"]
        or bool(followup_records)
        or followup_status_check_mentioned
    )
    indicators["main_internal_loop_success"] = (
        len(main_records) >= 2 or main_native_skill_tool_calls >= 2
    )
    indicators["followup_internal_loop_success"] = (
        len(followup_new) >= 2 or followup_native_skill_tool_calls >= 2
    )
    indicators["status_flow_triggered"] = (
        indicators["initial_checkpoint_success"]
        or indicators["followup_checkpoint_success"]
    )
    indicators["edit_success"] = all(
        indicators[key]
        for key in (
            "skill_edit_artifact_success",
            "auxiliary_artifact_success",
            "ledger_path_non_hidden",
        )
    )
    indicators["strict_e2e_success"] = all(
        indicators[key]
        for key in (
            "edit_success",
            "main_internal_loop_success",
            "followup_internal_loop_success",
        )
    )

    counters = {
        "auxiliary_skill_count": len(auxiliary_skills),
        "ledger_records_main": len(main_records),
        "ledger_records_followup": len(followup_records),
        "ledger_records_followup_new": len(followup_new),
        "ledger_records_total": max(len(main_records), len(followup_records)),
        "ledger_path_count": len(ledger_blocks),
        "native_skill_tool_calls": count_native_skill_activity(combined, auxiliary_skill),
        "main_native_skill_tool_calls": main_native_skill_tool_calls,
        "followup_native_skill_tool_calls": followup_native_skill_tool_calls,
        "slash_skill_call_evidence": len(SLASH_SKILL_RE.findall(combined)),
    }

    return {
        "indicators": indicators,
        "counters": counters,
        "evidence": {
            "skill_names": sorted(skills),
            "auxiliary_skill_names": auxiliary_skills,
            "ledger_paths": sorted(ledger_blocks),
            "followup_new_records": followup_new,
        },
        "summary_fields": summary_fields(indicators, counters),
    }


def _explain_code_modified(body: str, auxiliary_skill: str) -> bool:
    if not body:
        return False
    lowered = body.lower()
    return auxiliary_skill in lowered or "final consistency/status check" in lowered


def _baseline_purpose_preserved(body: str) -> bool:
    return all(marker in body for marker in BASELINE_MARKERS)


def _new_records(
    main_records: Iterable[dict[str, Any]],
    followup_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    main_keys = {record_key(record) for record in main_records}
    return [record for record in followup_records if record_key(record) not in main_keys]


def summary_fields(indicators: dict[str, bool], counters: dict[str, int]) -> dict[str, str]:
    return {
        "run_status": "Success" if indicators["runner_succeeded"] else "Failed",
        "edit_success": "Yes" if indicators["edit_success"] else "No",
        "auxiliary_skill": "Yes" if indicators["auxiliary_skill_created"] else "No",
        "exactly_one_auxiliary": "Yes"
        if indicators["exactly_one_auxiliary_skill"]
        else "No",
        "ledger_records": str(
            max(counters["ledger_records_main"], counters["ledger_records_followup"])
        ),
        "followup_new_records": str(counters["ledger_records_followup_new"]),
        "status_flow": "Yes" if indicators["status_flow_triggered"] else "No",
        "strict_e2e": "Yes" if indicators["strict_e2e_success"] else "No",
    }


def update_metrics_file(metrics_path: str | Path, report: dict[str, Any]) -> None:
    path = Path(metrics_path)
    metrics = json.loads(path.read_text()) if path.exists() else {}
    metrics.setdefault("indicators", {}).update(report["indicators"])
    metrics.setdefault("counters", {}).update(report["counters"])
    metrics.setdefault("analysis", {}).update(report)
    path.write_text(json.dumps(metrics, indent=2) + "\n")


def build_report_from_files(
    output_path: str | Path,
    followup_path: str | Path | None,
    state_paths: Iterable[str | Path],
    baseline_skill: str = BASELINE_SKILL,
    auxiliary_skill: str = AUXILIARY_SKILL,
) -> dict[str, Any]:
    return scan_edit_skill_evidence(
        read_text(output_path),
        followup_text=read_text(followup_path),
        state_paths=state_paths,
        baseline_skill=baseline_skill,
        auxiliary_skill=auxiliary_skill,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--followup")
    parser.add_argument("--state-file", action="append", default=[])
    parser.add_argument("--metrics")
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--baseline-skill", default=BASELINE_SKILL)
    parser.add_argument("--auxiliary-skill", default=AUXILIARY_SKILL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report_from_files(
        args.output,
        args.followup,
        args.state_file,
        baseline_skill=args.baseline_skill,
        auxiliary_skill=args.auxiliary_skill,
    )
    Path(args.analysis).write_text(json.dumps(report, indent=2) + "\n")
    if args.metrics:
        update_metrics_file(args.metrics, report)


if __name__ == "__main__":
    main()
