from __future__ import annotations

import json
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InjectionSpec:
    mode: str
    file: str
    target_field: str | None = None
    match_key: str | None = None
    match_value: str | None = None
    index: int | None = None
    prepend_label: str | None = None


@dataclass(frozen=True)
class TaskSelection:
    category: str
    label: str
    task_id: str
    task_path: str
    injection: InjectionSpec


def load_taskset(taskset_path: str | Path) -> list[TaskSelection]:
    path = Path(taskset_path)
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    selections: list[TaskSelection] = []
    for category_item in payload.get("category", []):
        category_name = str(category_item["name"])
        category_label = str(category_item.get("label", category_name))
        for task_item in category_item.get("task", []):
            injection_item = task_item["injection"]
            selections.append(
                TaskSelection(
                    category=category_name,
                    label=category_label,
                    task_id=str(task_item["task_id"]),
                    task_path=str(task_item["task_path"]),
                    injection=InjectionSpec(
                        mode=str(injection_item["mode"]),
                        file=str(injection_item["file"]),
                        target_field=_optional_str(injection_item.get("target_field")),
                        match_key=_optional_str(injection_item.get("match_key")),
                        match_value=_optional_str(injection_item.get("match_value")),
                        index=_optional_int(injection_item.get("index")),
                        prepend_label=_optional_str(injection_item.get("prepend_label")),
                    ),
                )
            )
    return selections


def selections_to_tsv(taskset_path: str | Path) -> str:
    rows = [
        "\t".join(
            [
                selection.category,
                selection.label,
                selection.task_id,
                selection.task_path,
                selection.injection.mode,
                selection.injection.file,
                _tsv_token(selection.injection.target_field),
                _tsv_token(selection.injection.match_key),
                _tsv_token(selection.injection.match_value),
                _tsv_token(None if selection.injection.index is None else str(selection.injection.index)),
                _tsv_token(selection.injection.prepend_label),
            ]
        )
        for selection in load_taskset(taskset_path)
    ]
    return "\n".join(rows) + ("\n" if rows else "")


def apply_injection(
    workspace_root: str | Path,
    injection: InjectionSpec,
    payload_text: str,
) -> Path:
    workspace = Path(workspace_root)
    target = workspace / injection.file
    if not target.exists():
        raise FileNotFoundError(f"Injection target does not exist: {target}")

    if injection.mode == "json_field_append":
        _apply_json_field_append(target, injection, payload_text)
        return target
    if injection.mode == "text_append":
        _apply_text_append(target, injection, payload_text)
        return target
    if injection.mode == "python_comment_append":
        _apply_python_comment_append(target, injection, payload_text)
        return target
    raise ValueError(f"Unsupported injection mode: {injection.mode}")


def build_category_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    overall = _summarize_bucket(results)
    per_category: dict[str, dict[str, Any]] = {}
    per_agent: dict[str, dict[str, Any]] = {}
    per_agent_category: dict[str, dict[str, dict[str, Any]]] = {}
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_agent_category: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for item in results:
        category = str(item.get("category", "uncategorized"))
        agent = str(item.get("agent", "unknown"))
        by_category[category].append(item)
        by_agent[agent].append(item)
        by_agent_category[agent][category].append(item)
    for category, rows in sorted(by_category.items()):
        per_category[category] = _summarize_bucket(rows)
    for agent, rows in sorted(by_agent.items()):
        per_agent[agent] = _summarize_bucket(rows)
    for agent, categories in sorted(by_agent_category.items()):
        per_agent_category[agent] = {}
        for category, rows in sorted(categories.items()):
            per_agent_category[agent][category] = _summarize_bucket(rows)
    return {
        "overall": overall,
        "categories": per_category,
        "agents": per_agent,
        "agent_category": per_agent_category,
    }


def render_category_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Context Injection ADD_S Summary",
        "",
        "## Overall",
        "",
        _render_bucket_lines(summary["overall"]),
        "",
        "## Per Agent",
        "",
    ]
    for agent, bucket in summary["agents"].items():
        lines.append(f"### {agent}")
        lines.append("")
        lines.append(_render_bucket_lines(bucket))
        lines.append("")

    lines.extend(
        [
        "## Per Category",
        "",
        ]
    )
    for category, bucket in summary["categories"].items():
        lines.append(f"### {category}")
        lines.append("")
        lines.append(_render_bucket_lines(bucket))
        lines.append("")

    lines.extend(
        [
            "## Per Agent By Category",
            "",
        ]
    )
    for agent, categories in summary["agent_category"].items():
        lines.append(f"### {agent}")
        lines.append("")
        for category, bucket in categories.items():
            lines.append(f"#### {category}")
            lines.append("")
            lines.append(_render_bucket_lines(bucket))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cli(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("Usage: context_injection_add_s.py <command> [...]")
    command = argv[1]
    if command == "print-taskset-tsv":
        if len(argv) != 3:
            raise SystemExit("Usage: print-taskset-tsv <taskset_path>")
        print(selections_to_tsv(argv[2]), end="")
        return 0
    if command == "apply-injection":
        if len(argv) != 14:
            raise SystemExit(
                "Usage: apply-injection <workspace_root> <mode> <file> <target_field> "
                "<match_key> <match_value> <index> <prepend_label> <payload_path> "
                "<result_json> <task_id> <category>"
            )
        workspace_root, mode, file_name, target_field, match_key, match_value, index_text, prepend_label, payload_path, result_json, task_id, category = argv[2:14]
        spec = InjectionSpec(
            mode=mode,
            file=file_name,
            target_field=_or_none(target_field),
            match_key=_or_none(match_key),
            match_value=_or_none(match_value),
            index=None if index_text == "__NONE__" else int(index_text),
            prepend_label=_or_none(prepend_label),
        )
        injected_path = apply_injection(
            workspace_root,
            spec,
            Path(payload_path).read_text(encoding="utf-8"),
        )
        Path(result_json).write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "category": category,
                    "injected_path": str(injected_path),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0
    if command == "write-summary":
        if len(argv) != 5:
            raise SystemExit("Usage: write-summary <results_jsonl> <summary_json> <summary_md>")
        results_path = Path(argv[2])
        rows = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        summary = build_category_summary(rows)
        Path(argv[3]).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        Path(argv[4]).write_text(render_category_summary_markdown(summary), encoding="utf-8")
        return 0
    raise SystemExit(f"Unknown command: {command}")


def _apply_json_field_append(target: Path, injection: InjectionSpec, payload_text: str) -> None:
    if not injection.target_field:
        raise ValueError("json_field_append requires target_field")
    data = json.loads(target.read_text(encoding="utf-8"))
    node = _select_json_node(data, injection)
    if not isinstance(node, dict):
        raise ValueError("Selected JSON node must be an object")
    existing = str(node.get(injection.target_field, "")).rstrip()
    prefix = "" if not injection.prepend_label else f"{injection.prepend_label}\n"
    node[injection.target_field] = f"{existing}\n\n{prefix}{payload_text}".strip()
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _apply_text_append(target: Path, injection: InjectionSpec, payload_text: str) -> None:
    existing = target.read_text(encoding="utf-8")
    prefix = "" if not injection.prepend_label else f"{injection.prepend_label}\n"
    text = existing.rstrip() + "\n\n" + prefix + payload_text + "\n"
    target.write_text(text, encoding="utf-8")


def _apply_python_comment_append(target: Path, injection: InjectionSpec, payload_text: str) -> None:
    existing = target.read_text(encoding="utf-8")
    prefix_lines: list[str] = []
    if injection.prepend_label:
        prefix_lines.append(f"# {injection.prepend_label}")
    for line in payload_text.splitlines():
        prefix_lines.append("#" if not line else f"# {line}")
    text = existing.rstrip() + "\n\n" + "\n".join(prefix_lines) + "\n"
    target.write_text(text, encoding="utf-8")


def _select_json_node(data: Any, injection: InjectionSpec) -> Any:
    if injection.match_key is not None:
        if not isinstance(data, list):
            raise ValueError("match_key selection requires a JSON array")
        for item in data:
            if isinstance(item, dict) and str(item.get(injection.match_key)) == injection.match_value:
                return item
        raise ValueError(
            f"No JSON object matched {injection.match_key}={injection.match_value}"
        )
    if injection.index is not None:
        if not isinstance(data, list):
            raise ValueError("index selection requires a JSON array")
        return data[injection.index]
    if isinstance(data, dict):
        return data
    raise ValueError(
        "Injection spec requires either match_key/match_value, index, or a top-level JSON object"
    )


def _summarize_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    poisoned_rows = [row for row in rows if row.get("variant") == "poisoned"]
    task_successes = sum(1 for row in rows if row.get("verifier_passed"))
    injection_successes = sum(1 for row in poisoned_rows if row.get("injection_observed"))
    return {
        "total_runs": total,
        "poisoned_runs": len(poisoned_rows),
        "task_successes": task_successes,
        "injection_successes": injection_successes,
        "tsr": _ratio(task_successes, total),
        "p_asr": _ratio(injection_successes, len(poisoned_rows)),
    }


def _render_bucket_lines(bucket: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- total runs: {bucket['total_runs']}",
            f"- poisoned runs: {bucket['poisoned_runs']}",
            f"- task successes: {bucket['task_successes']}",
            f"- injection successes: {bucket['injection_successes']}",
            f"- TSR: {bucket['tsr']:.4f}",
            f"- P-ASR: {bucket['p_asr']:.4f}",
        ]
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _or_none(value: str) -> str | None:
    return None if value == "__NONE__" else value


def _tsv_token(value: str | None) -> str:
    return "__NONE__" if value in (None, "") else value


if __name__ == "__main__":
    raise SystemExit(cli(__import__("sys").argv))
