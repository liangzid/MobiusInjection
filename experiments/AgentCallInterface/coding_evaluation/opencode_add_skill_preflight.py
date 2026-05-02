"""Gate 4-8 preflight suite for cross-model OpenCode add-skill Mobius runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on runner Python.
    tomllib = None

from experiments.AgentCallInterface.coding_agents.coding_agent_callers import get_caller
from experiments.AgentCallInterface.coding_datasets.coding_benchmark_loader import (
    HumanEvalLoader,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PROJECT_ROOT / "experiments/configs/cross_model_opencode_add_skill_mobius_models.toml"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "experiments/results/preflight_opencode_add_skill_mobius"
RESET_SCRIPT = PROJECT_ROOT / "experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh"
TEMPLATE_PATH = PROJECT_ROOT / "mobiusInjection/CODING_AGENT_TEMPLATE_OPENCODE_V10_REALISTIC.py"
MONITOR_PATH = PROJECT_ROOT / "experiments/AgentCallInterface/coding_evaluation/opencode_recursive_trace_monitor.py"


@dataclass(frozen=True)
class ModelConfig:
    label: str
    model_id: str
    enabled: bool
    provider: str
    timeout_seconds: int
    candidate_name: str
    resolution_note: str


@dataclass(frozen=True)
class TaskConfig:
    dataset: str
    task_id: str
    prompt: str


def load_model_configs(path: str | Path) -> list[ModelConfig]:
    text = Path(path).read_text(encoding="utf-8")
    payload = tomllib.loads(text) if tomllib else parse_minimal_toml(text)
    models = []
    for item in payload.get("models", []):
        models.append(
            ModelConfig(
                label=str(item["label"]),
                model_id=str(item["model_id"]),
                enabled=bool(item.get("enabled", True)),
                provider=str(item.get("provider", "openrouter")),
                timeout_seconds=int(item.get("timeout_seconds", 300)),
                candidate_name=str(item.get("candidate_name", item["label"])),
                resolution_note=str(item.get("resolution_note", "")),
            )
        )
    validate_model_configs(models)
    return models


def parse_minimal_toml(text: str) -> dict[str, Any]:
    models: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line == "[[models]]":
            current = {}
            models.append(current)
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        current[key] = parse_minimal_toml_value(value)
    return {"models": models}


def parse_minimal_toml_value(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def validate_model_configs(models: list[ModelConfig]) -> None:
    labels = [model.label for model in models]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise ValueError(f"duplicate model labels: {duplicates}")
    unresolved = [model.label for model in models if model.enabled and not model.model_id.strip()]
    if unresolved:
        raise ValueError(f"enabled model labels without model_id: {unresolved}")


def load_humaneval_tasks(limit: int) -> list[TaskConfig]:
    raw_tasks = HumanEvalLoader().load_benchmark_tasks(limit=limit)
    return [
        TaskConfig(dataset="humaneval", task_id=task.task_id, prompt=task.prompt)
        for task in raw_tasks
    ]


def make_run_dir(output_root: str | Path, prefix: str = "preflight") -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = Path(output_root) / f"{prefix}_{stamp}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def build_manifest(
    *,
    run_dir: Path,
    models: list[ModelConfig],
    tasks: list[TaskConfig],
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    manifest = []
    for model in models:
        if not model.enabled:
            continue
        for task in tasks:
            case_id = f"{model.label}_{task.task_id.replace('/', '_')}"
            manifest.append(
                {
                    "case_id": case_id,
                    "model_label": model.label,
                    "model_id": model.model_id,
                    "provider": model.provider,
                    "dataset": task.dataset,
                    "task_id": task.task_id,
                    "agent": "opencode",
                    "timeout_seconds": timeout_seconds or model.timeout_seconds,
                    "run_directory": str(run_dir / "cases" / case_id),
                    "prompt_hash": prompt_hash(task.prompt),
                    "candidate_name": model.candidate_name,
                    "resolution_note": model.resolution_note,
                }
            )
    return manifest


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_reset(output_path: Path, timeout: int = 60) -> int:
    with output_path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            [str(RESET_SCRIPT)],
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    return result.returncode


def call_opencode(prompt: str, task_id: str, model_id: str, timeout: int):
    caller = get_caller("opencode")
    return caller.call(
        {"task_id": task_id, "problem_statement": prompt},
        timeout=timeout,
        model=model_id,
    )


def response_payload(response) -> dict[str, Any]:
    return {
        "success": response.success,
        "duration": response.duration,
        "task_id": response.task_id,
        "returncode": response.returncode,
        "output": response.output,
        "error": response.error,
        "stderr": response.stderr,
    }


def write_response(path: Path, response) -> None:
    write_json(path, response_payload(response))


def classify_connectivity(response_payload: dict[str, Any]) -> str:
    text = "\n".join(
        str(response_payload.get(key) or "")
        for key in ("output", "error", "stderr")
    ).lower()
    if response_payload.get("success") and str(response_payload.get("output") or "").strip():
        return "ok"
    if "timeout" in text:
        return "timeout"
    if "unauthorized" in text or "401" in text or "auth" in text and "error" in text:
        return "auth"
    if "rate limit" in text or "429" in text:
        return "rate_limit"
    if "model not found" in text or "providermodelnotfound" in text:
        return "model_unavailable"
    if "api error" in text or "provider" in text:
        return "provider_error"
    if "connection" in text or "network" in text or "dns" in text:
        return "network_error"
    return "runtime_error"


def connectivity_prompt(label: str) -> str:
    return (
        "Reply with exactly one short line in the form "
        f"`CONNECTIVITY_OK {label}`. Do not use tools."
    )


def run_connectivity_matrix(
    *,
    run_dir: Path,
    models: list[ModelConfig],
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    rows = []
    output_dir = run_dir / "connectivity"
    output_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        if not model.enabled:
            continue
        case_dir = output_dir / model.label
        case_dir.mkdir(parents=True, exist_ok=True)
        reset_status = run_reset(case_dir / "reset.txt")
        start = time.time()
        response = call_opencode(
            connectivity_prompt(model.label),
            f"connectivity_{model.label}",
            model.model_id,
            timeout_seconds or min(model.timeout_seconds, 120),
        )
        payload = response_payload(response)
        write_json(case_dir / "response.json", payload)
        status = classify_connectivity(payload)
        rows.append(
            {
                "model_label": model.label,
                "model_id": model.model_id,
                "provider": model.provider,
                "status": status,
                "success": status == "ok",
                "duration_seconds": round(time.time() - start, 3),
                "response_seconds": round(response.duration, 3),
                "reset_status": reset_status,
                "response_file": str(case_dir / "response.json"),
                "resolution_note": model.resolution_note,
            }
        )
    write_json(output_dir / "connectivity_matrix.json", rows)
    write_csv(output_dir / "connectivity_matrix.csv", rows)
    write_connectivity_report(output_dir / "model_connectivity_report.md", rows)
    return rows


def run_timeout_cleanup_probe(
    *,
    run_dir: Path,
    model: ModelConfig,
    timeout_seconds: int,
) -> dict[str, Any]:
    output_dir = run_dir / "timeout_cleanup"
    output_dir.mkdir(parents=True, exist_ok=True)
    before_images = docker_images()
    reset_status = run_reset(output_dir / "reset_before.txt")
    prompt = "Use bash to run `sleep 20`, then reply `SLEEP_DONE`."
    response = call_opencode(
        prompt,
        f"timeout_cleanup_{model.label}",
        model.model_id,
        timeout_seconds,
    )
    payload = response_payload(response)
    write_json(output_dir / "response.json", payload)
    process_check = docker_exec_text(
        "pgrep -af '[/]root/.opencode/bin/opencode run --dir /opencode' || true"
    )
    after_reset_status = run_reset(output_dir / "reset_after.txt")
    after_images = docker_images()
    result = {
        "model_label": model.label,
        "model_id": model.model_id,
        "response_success": response.success,
        "timed_out": classify_connectivity(payload) == "timeout",
        "reset_before_status": reset_status,
        "reset_after_status": after_reset_status,
        "opencode_processes_after_timeout": process_check.strip(),
        "opencode_process_cleanup_success": process_check.strip() == "",
        "docker_image_count_before": len(before_images),
        "docker_image_count_after": len(after_images),
        "docker_image_count_unchanged": len(before_images) == len(after_images),
        "docker_commit_used": False,
    }
    write_json(output_dir / "timeout_cleanup_report.json", result)
    return result


def docker_exec_text(script: str, timeout: int = 10) -> str:
    result = subprocess.run(
        ["docker", "exec", "opencode", "bash", "-lc", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return "\n".join(part for part in (result.stdout, result.stderr) if part)


def docker_images() -> list[str]:
    result = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.ID}}"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def smoke_prompt(task: TaskConfig) -> str:
    return (
        "You are running a short smoke test for the upcoming benchmark. "
        "Read the task and answer with a one-sentence implementation strategy; "
        "do not create files.\n\n"
        f"Task:\n{task.prompt}"
    )


def run_aggregation_smoke(
    *,
    run_dir: Path,
    models: list[ModelConfig],
    tasks: list[TaskConfig],
    timeout_seconds: int,
) -> dict[str, Any]:
    smoke_dir = run_dir / "aggregation_smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for model in models[:2]:
        for task in tasks[:2]:
            case_id = f"{model.label}_{task.task_id.replace('/', '_')}"
            case_dir = smoke_dir / "cases" / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            reset_status = run_reset(case_dir / "reset.txt")
            response = call_opencode(
                smoke_prompt(task),
                f"smoke_{case_id}",
                model.model_id,
                timeout_seconds,
            )
            write_response(case_dir / "response.json", response)
            status = classify_connectivity(response_payload(response))
            cases.append(
                {
                    "case_id": case_id,
                    "model_label": model.label,
                    "model_id": model.model_id,
                    "provider": model.provider,
                    "dataset": task.dataset,
                    "task_id": task.task_id,
                    "agent": "opencode",
                    "status": status,
                    "TSR": status == "ok",
                    "P_ASR": False,
                    "T_ASR": False,
                    "R_ASR": False,
                    "STRICT_E2E_ASR": False,
                    "timeout": status == "timeout",
                    "runtime_failure": status not in {"ok", "timeout"},
                    "duration_seconds": round(response.duration, 3),
                    "raw_log": str(case_dir / "response.json"),
                    "reset_status": reset_status,
                }
            )
    result = aggregate_smoke_cases(smoke_dir, cases)
    write_result_package(smoke_dir, result)
    return result


def aggregate_smoke_cases(smoke_dir: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_dir": str(smoke_dir),
        "run_config": {
            "agent": "opencode",
            "smoke_shape": "2 models x 2 tasks",
            "template_path": str(TEMPLATE_PATH),
            "monitor_path": str(MONITOR_PATH),
        },
        "aggregate": summarize_cases(cases),
        "models": group_summary(cases, "model_label"),
        "tasks": group_summary(cases, "task_id"),
        "cases": cases,
    }


def summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(cases)
    if total == 0:
        return empty_summary()
    return {
        "N": total,
        "TSR": rate(cases, "TSR"),
        "P_ASR": rate(cases, "P_ASR"),
        "T_ASR": rate(cases, "T_ASR"),
        "R_ASR": rate(cases, "R_ASR"),
        "STRICT_E2E_ASR": rate(cases, "STRICT_E2E_ASR"),
        "trace_alternation_rate": 0.0,
        "trace_rounds_avg": 0.0,
        "timeout_rate": rate(cases, "timeout"),
        "runtime_failure_rate": rate(cases, "runtime_failure"),
    }


def empty_summary() -> dict[str, Any]:
    return {
        "N": 0,
        "TSR": 0.0,
        "P_ASR": 0.0,
        "T_ASR": 0.0,
        "R_ASR": 0.0,
        "STRICT_E2E_ASR": 0.0,
        "trace_alternation_rate": 0.0,
        "trace_rounds_avg": 0.0,
        "timeout_rate": 0.0,
        "runtime_failure_rate": 0.0,
    }


def rate(cases: list[dict[str, Any]], key: str) -> float:
    return sum(1 for case in cases if case.get(key)) / len(cases) if cases else 0.0


def group_summary(cases: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        groups.setdefault(str(case[key]), []).append(case)
    return {name: summarize_cases(items) for name, items in sorted(groups.items())}


def write_result_package(run_dir: Path, result: dict[str, Any]) -> None:
    write_json(run_dir / "metrics.json", result)
    write_json(run_dir / "trace_metrics.json", {"cases": trace_rows(result["cases"])})
    write_json(run_dir / "run_config_snapshot.json", result["run_config"])
    write_json(run_dir / "run_manifest.json", result["cases"])
    write_csv(run_dir / "case_metrics.csv", result["cases"])
    write_csv(run_dir / "agent_metrics.csv", summary_rows({"opencode": result["aggregate"]}, "agent"))
    write_csv(run_dir / "model_metrics.csv", summary_rows(result["models"], "model_label"))
    write_csv(run_dir / "task_metrics.csv", summary_rows(result["tasks"], "task_id"))
    write_csv(run_dir / "trace_case_metrics.csv", trace_rows(result["cases"]))
    write_metrics_report(run_dir / "metrics_report.md", result)
    write_readme(run_dir / "README.md", result)
    write_failure_examples(run_dir / "failure_examples.md", result["cases"])


def trace_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case["case_id"],
            "model_label": case["model_label"],
            "task_id": case["task_id"],
            "trace_record_count": 0,
            "valid_trace_record_count": 0,
            "trace_rounds_main": 0,
            "trace_rounds_followup_new": 0,
            "trace_alternation_success": False,
        }
        for case in cases
    ]


def summary_rows(groups: dict[str, dict[str, Any]], label_name: str) -> list[dict[str, Any]]:
    rows = []
    for label, summary in groups.items():
        row = {label_name: label}
        row.update(summary)
        rows.append(row)
    return rows


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metrics_report(path: Path, result: dict[str, Any]) -> None:
    lines = ["# Metrics Report", "", "## Overall", "", markdown_summary(result["aggregate"])]
    lines.extend(["", "## Per Model", "", markdown_table(summary_rows(result["models"], "model_label"))])
    lines.extend(["", "## Per Task", "", markdown_table(summary_rows(result["tasks"], "task_id"))])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# OpenCode Add-Skill Mobius Preflight Smoke",
        "",
        "This directory is a packaging smoke test for the final cross-model add-skill run.",
        "It uses real OpenCode calls, but does not run the add-skill injection payload.",
        "",
        f"Total cases: {result['aggregate']['N']}",
        "Agent: OpenCode only",
        f"Template path: `{TEMPLATE_PATH}`",
        f"Monitor path: `{MONITOR_PATH}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_examples(path: Path, cases: list[dict[str, Any]]) -> None:
    failures = [case for case in cases if case["status"] != "ok"]
    lines = ["# Failure Examples", ""]
    if not failures:
        lines.append("No smoke failures recorded.")
    for case in failures:
        lines.append(f"- `{case['case_id']}`: `{case['status']}`; log `{case['raw_log']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_connectivity_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# Model Connectivity Report", "", markdown_table(rows)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def markdown_summary(summary: dict[str, Any]) -> str:
    return "\n".join(f"- `{key}`: {value}" for key, value in summary.items())


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


def build_scheduling_summary(
    connectivity: list[dict[str, Any]],
    timeout_cleanup: dict[str, Any],
) -> dict[str, Any]:
    ok_rows = [row for row in connectivity if row["status"] == "ok"]
    latencies = [row["response_seconds"] for row in ok_rows]
    return {
        "enabled_model_count": len(connectivity),
        "connectivity_success_count": len(ok_rows),
        "connectivity_failures": [
            {"model_label": row["model_label"], "status": row["status"]}
            for row in connectivity
            if row["status"] != "ok"
        ],
        "latency_seconds_min": min(latencies) if latencies else None,
        "latency_seconds_max": max(latencies) if latencies else None,
        "latency_seconds_avg": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "timeout_cleanup_success": bool(
            timeout_cleanup.get("opencode_process_cleanup_success")
            and timeout_cleanup.get("docker_image_count_unchanged")
        ),
        "recommended_policy": (
            "Run model-serial and task-serial for the first full experiment; "
            "increase concurrency only after reset and cleanup remain stable."
        ),
        "recommended_case_timeout_seconds": 300,
    }


def run_suite(args: argparse.Namespace) -> Path:
    run_dir = make_run_dir(args.output_root, "gates_4_8")
    models = load_model_configs(args.config)
    tasks = load_humaneval_tasks(max(args.task_limit, 2))
    manifest = build_manifest(
        run_dir=run_dir,
        models=models,
        tasks=tasks[: args.task_limit],
        timeout_seconds=args.case_timeout,
    )
    write_json(run_dir / "run_manifest.json", manifest)
    write_json(run_dir / "model_config_snapshot.json", [asdict(model) for model in models])
    write_json(
        run_dir / "run_config_snapshot.json",
        {
            "agent": "opencode",
            "dataset": "humaneval",
            "task_limit": args.task_limit,
            "case_timeout": args.case_timeout,
            "template_path": str(TEMPLATE_PATH),
            "monitor_path": str(MONITOR_PATH),
            "config": str(args.config),
        },
    )
    connectivity = run_connectivity_matrix(
        run_dir=run_dir,
        models=models,
        timeout_seconds=args.connectivity_timeout,
    )
    smoke_models = pick_smoke_models(models, connectivity)
    smoke_result = run_aggregation_smoke(
        run_dir=run_dir,
        models=smoke_models,
        tasks=tasks,
        timeout_seconds=args.smoke_timeout,
    )
    timeout_model = smoke_models[0] if smoke_models else next(model for model in models if model.enabled)
    cleanup = run_timeout_cleanup_probe(
        run_dir=run_dir,
        model=timeout_model,
        timeout_seconds=args.timeout_probe_seconds,
    )
    scheduling = build_scheduling_summary(connectivity, cleanup)
    write_json(run_dir / "scheduling_summary.json", scheduling)
    write_gate_report(run_dir / "gate_4_8_report.md", manifest, connectivity, cleanup, smoke_result, scheduling)
    return run_dir


def pick_smoke_models(
    models: list[ModelConfig], connectivity: list[dict[str, Any]]
) -> list[ModelConfig]:
    ok_labels = [row["model_label"] for row in connectivity if row["status"] == "ok"]
    by_label = {model.label: model for model in models}
    picked = [by_label[label] for label in ok_labels[:2] if label in by_label]
    if len(picked) >= 2:
        return picked
    for model in models:
        if model.enabled and model not in picked:
            picked.append(model)
        if len(picked) == 2:
            break
    return picked


def write_gate_report(
    path: Path,
    manifest: list[dict[str, Any]],
    connectivity: list[dict[str, Any]],
    cleanup: dict[str, Any],
    smoke_result: dict[str, Any],
    scheduling: dict[str, Any],
) -> None:
    lines = [
        "# Gate 4-8 OpenCode Add-Skill Preflight Report",
        "",
        "## Gate 4 - External Model Configuration Dry Run",
        "",
        f"- Planned cases: {len(manifest)}",
        "- Agent: OpenCode only",
        "- Invalid enabled model labels: none",
        "",
        "## Gate 5 - Connectivity Matrix",
        "",
        markdown_table(connectivity),
        "",
        "## Gate 6 - Timeout And Cleanup",
        "",
        markdown_summary(cleanup),
        "",
        "## Gate 7 - Aggregation Smoke",
        "",
        f"- Smoke run directory: `{smoke_result['run_dir']}`",
        markdown_summary(smoke_result["aggregate"]),
        "",
        "## Gate 8 - Cost, Rate Limit, And Scheduling",
        "",
        markdown_summary(scheduling),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--task-limit", type=int, default=1)
    parser.add_argument("--case-timeout", type=int, default=300)
    parser.add_argument("--connectivity-timeout", type=int, default=90)
    parser.add_argument("--smoke-timeout", type=int, default=90)
    parser.add_argument("--timeout-probe-seconds", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    run_dir = run_suite(parse_args())
    print(run_dir)


if __name__ == "__main__":
    main()
