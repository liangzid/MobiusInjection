#!/usr/bin/env python3
"""Run Plan C OpenCode multi-zombie scaling on local Ollama."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path("/home/zi/AgentCodingDos")
BASE_RUNNER_PATH = (
    REPO
    / "experiments/results/opencode_datadog_fileedit_ollama_20260503/run_datadog_fileedit_ollama.py"
)
ROOT = REPO / "experiments/results/opencode_multizombie_scaling_20260504"
PROXY_LOG = Path(
    "/data2/zi/agentcodingdos_plan_c_logs/opencode_multizombie_scaling_20260504/"
    "ollama_proxy.jsonl"
)
BASELINE_SETUP = (
    REPO / "experiments/results/opencode_datadog_fileedit_ollama_20260503/clean_setup_before.py"
)
TRACE_PATH = "/opencode/.opencode/skills/post-edit-audit-record.jsonl"
THRESHOLDS = [30, 60, 90, 120, 180, 240, 300, 420, 600]


@dataclass(frozen=True)
class AgentSpec:
    condition: str
    agent_count: int
    agent_index: int
    container: str
    run_id: str
    timeout_seconds: int
    with_skills: bool


@dataclass(frozen=True)
class AgentResult:
    spec: AgentSpec
    success: bool
    timeout: bool
    duration_seconds: float
    returncode: int | None
    error: str
    output: str
    stderr: str
    trace_before: str
    trace_after: str
    setup_before: str
    setup_after: str
    diff: str


@dataclass(frozen=True)
class GroupResult:
    condition: str
    agent_count: int
    timeout_seconds: int
    started_at: float
    proxy_start_line: int
    proxy_end_line: int
    agent_results: tuple[AgentResult, ...]


def load_base_runner() -> Any:
    spec = importlib.util.spec_from_file_location("opencode_datadog_base_runner", BASE_RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load base runner from {BASE_RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.PROXY_LOG = PROXY_LOG
    return module


BASE = load_base_runner()


def run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def require_ok(result: subprocess.CompletedProcess[str], action: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(f"{action} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def start_background(cmd: list[str], stdout_path: Path, stderr_path: Path) -> subprocess.Popen[Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("a", encoding="utf-8")
    stderr = stderr_path.open("a", encoding="utf-8")
    return subprocess.Popen(cmd, stdout=stdout, stderr=stderr, text=True)


def wait_for_port(port: int, seconds: int = 60) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if port_open(port):
            return
        time.sleep(0.5)
    raise RuntimeError(f"port {port} did not open")


def ensure_services() -> list[subprocess.Popen[Any]]:
    processes: list[subprocess.Popen[Any]] = []
    if not port_open(11437):
        processes.append(
            start_background(
                [
                    "env",
                    "OLLAMA_HOST=127.0.0.1:11437",
                    "OLLAMA_MODELS=/data2/zi/ollama_models",
                    "OLLAMA_NUM_PARALLEL=1",
                    "CUDA_VISIBLE_DEVICES=1",
                    "/data2/zi/ollama_v0.22.1/bin/ollama",
                    "serve",
                ],
                ROOT / "ollama_stdout.log",
                ROOT / "ollama_stderr.log",
            )
        )
        wait_for_port(11437)
    if not port_open(11436):
        processes.append(
            start_background(
                [
                    "uv",
                    "run",
                    "python",
                    str(REPO / "localserver/ollama_proxy_logger.py"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "11436",
                    "--upstream",
                    "http://127.0.0.1:11437",
                    "--log-path",
                    str(PROXY_LOG),
                ],
                ROOT / "proxy_stdout.log",
                ROOT / "proxy_stderr.log",
            )
        )
        wait_for_port(11436)
    return processes


def stop_processes(processes: list[subprocess.Popen[Any]]) -> None:
    for process in processes:
        process.terminate()
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))


def docker_exec(container: str, script: str, timeout: int = 30) -> str:
    result = run(["docker", "exec", container, "bash", "-lc", script], timeout=timeout)
    return (result.stdout + result.stderr).strip()


def prepare_container(spec: AgentSpec) -> None:
    BASE.recreate_container(spec.container)
    require_ok(
        run(
            [
                "docker",
                "exec",
                spec.container,
                "bash",
                "-lc",
                "set -euo pipefail; "
                "mkdir -p /opencode/active_directory /opencode/.opencode/skills; "
                "rm -rf /opencode/.opencode/skills/*",
            ],
            timeout=60,
        ),
        f"prepare workspace in {spec.container}",
    )
    require_ok(
        run(["docker", "cp", str(BASELINE_SETUP), f"{spec.container}:/opencode/active_directory/setup.py"], timeout=60),
        f"copy real DataDog setup.py into {spec.container}",
    )
    require_ok(
        run(
            [
                "docker",
                "exec",
                spec.container,
                "bash",
                "-lc",
                "cp /opencode/active_directory/setup.py /tmp/datadog_setup_baseline.py",
            ],
            timeout=30,
        ),
        f"snapshot baseline setup.py in {spec.container}",
    )
    if spec.with_skills:
        for skill_dir in sorted(BASE.STAGING.iterdir()):
            if skill_dir.is_dir():
                require_ok(
                    run(["docker", "cp", str(skill_dir), f"{spec.container}:/opencode/.opencode/skills/"], timeout=60),
                    f"copy skill {skill_dir.name} into {spec.container}",
                )


def base_spec(spec: AgentSpec) -> Any:
    return BASE.RunSpec(
        condition=spec.condition,
        container=spec.container,
        with_skills=spec.with_skills,
        run_id=spec.run_id,
        timeout_seconds=spec.timeout_seconds,
    )


def capture_setup(container: str) -> str:
    return docker_exec(container, "sed -n '1,180p' /opencode/active_directory/setup.py 2>/dev/null || true")


def capture_trace(container: str) -> str:
    return docker_exec(container, f"cat {TRACE_PATH} 2>/dev/null || true")


def execute_prepared(spec: AgentSpec, prompt: str) -> AgentResult:
    setup_before = capture_setup(spec.container)
    trace_before = capture_trace(spec.container)
    cmd = BASE.build_opencode_command(base_spec(spec), prompt)
    start = time.time()
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
        duration = time.time() - start
        success = completed.returncode == 0 and "ProviderModelNotFoundError" not in completed.stderr
        timed_out = False
        stderr = completed.stderr or ""
        output = (completed.stdout or "") + ("\n=== STDERR ===\n" + stderr if stderr else "")
        error = "" if success else stderr or "OpenCode command failed"
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        duration = time.time() - start
        docker_exec(spec.container, "pkill -f '/root/.opencode/bin/opencode run --dir /opencode' || true")
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        output = stdout + ("\n=== STDERR ===\n" + stderr if stderr else "")
        success = False
        timed_out = True
        error = f"Timeout after {spec.timeout_seconds}s"
        returncode = None
    setup_after = capture_setup(spec.container)
    trace_after = capture_trace(spec.container)
    diff = docker_exec(
        spec.container,
        "diff -u /tmp/datadog_setup_baseline.py /opencode/active_directory/setup.py || true",
    )
    return AgentResult(
        spec=spec,
        success=success,
        timeout=timed_out,
        duration_seconds=duration,
        returncode=returncode,
        error=error,
        output=output,
        stderr=stderr,
        trace_before=trace_before,
        trace_after=trace_after,
        setup_before=setup_before,
        setup_after=setup_after,
        diff=diff,
    )


def proxy_entries(start_line: int, end_line: int) -> list[dict[str, Any]]:
    if not PROXY_LOG.exists():
        return []
    rows: list[dict[str, Any]] = []
    with PROXY_LOG.open("r", encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle):
            if index < start_line:
                continue
            if index >= end_line:
                break
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def is_chat_request(row: dict[str, Any]) -> bool:
    return str(row.get("path", "")).endswith("/chat/completions")


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile_value
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def trace_delta(result: AgentResult) -> int:
    after = BASE.trace_rows(result.trace_after, result.spec.run_id)
    before = BASE.trace_rows(result.trace_before, result.spec.run_id)
    return len(after) - len(before)


def setup_fixed(result: AgentResult) -> bool:
    return "'datadog-active-directory=datadog_checks.active_directory:main'" in result.setup_after


def agent_tool_counts(result: AgentResult) -> dict[str, int]:
    events = BASE.parse_json_events(result.output)
    tools = [event for event in events if event.get("type") == "tool_use"]
    skill_tools = [event for event in tools if BASE.event_tool_name(event) == "skill"]
    return {
        "native_tool_calls": len(tools),
        "skill_tool_loads": len(skill_tools),
        "file_edit_events": BASE.count_file_edit_events(tools),
    }


def group_summary_row(group: GroupResult) -> dict[str, Any]:
    entries = [row for row in proxy_entries(group.proxy_start_line, group.proxy_end_line) if is_chat_request(row)]
    latencies = [float(row.get("latency_ms") or 0.0) for row in entries]
    failed = [row for row in entries if int(row.get("status_code") or 0) >= 400]
    tool_counts = [agent_tool_counts(result) for result in group.agent_results]
    duration_minutes = max(group.timeout_seconds, 1) / 60.0
    total_requests = len(entries)
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in entries)
    return {
        "agent_count": group.agent_count,
        "condition": group.condition,
        "window_seconds": group.timeout_seconds,
        "agents_completed": sum(1 for result in group.agent_results if result.success),
        "agents_timed_out": sum(1 for result in group.agent_results if result.timeout),
        "max_duration_seconds": round(max(result.duration_seconds for result in group.agent_results), 2),
        "native_tool_calls": sum(row["native_tool_calls"] for row in tool_counts),
        "skill_tool_loads": sum(row["skill_tool_loads"] for row in tool_counts),
        "file_edit_events": sum(row["file_edit_events"] for row in tool_counts),
        "trace_delta": sum(trace_delta(result) for result in group.agent_results),
        "setup_fixed_agents": sum(1 for result in group.agent_results if setup_fixed(result)),
        "proxy_chat_requests": total_requests,
        "proxy_total_tokens": total_tokens,
        "requests_per_min": round(total_requests / duration_minutes, 3),
        "tokens_per_min": round(total_tokens / duration_minutes, 3),
        "p50_latency_ms": round(percentile(latencies, 0.50), 3),
        "p95_latency_ms": round(percentile(latencies, 0.95), 3),
        "p99_latency_ms": round(percentile(latencies, 0.99), 3),
        "failed_requests": len(failed),
        "failed_request_rate": round(len(failed) / total_requests, 4) if total_requests else 0.0,
        "proxy_start_line": group.proxy_start_line,
        "proxy_end_line": group.proxy_end_line,
    }


def cumulative_rows(group: GroupResult) -> list[dict[str, Any]]:
    entries = [row for row in proxy_entries(group.proxy_start_line, group.proxy_end_line) if is_chat_request(row)]
    rows: list[dict[str, Any]] = []
    for threshold in threshold_seconds(group.timeout_seconds):
        cutoff = group.started_at + threshold
        visible = [row for row in entries if float(row.get("ts") or 0.0) <= cutoff]
        latencies = [float(row.get("latency_ms") or 0.0) for row in visible]
        rows.append(
            {
                "elapsed_seconds": threshold,
                "agent_count": group.agent_count,
                "condition": group.condition,
                "proxy_chat_requests": len(visible),
                "proxy_total_tokens": sum(int(row.get("total_tokens") or 0) for row in visible),
                "p95_latency_ms": round(percentile(latencies, 0.95), 3),
                "failed_requests": sum(1 for row in visible if int(row.get("status_code") or 0) >= 400),
            }
        )
    return rows


def threshold_seconds(timeout_seconds: int) -> list[int]:
    values = [value for value in THRESHOLDS if value <= timeout_seconds]
    if timeout_seconds not in values:
        values.append(timeout_seconds)
    return values


def specs_for(agent_counts: list[int], conditions: list[str], timeout_seconds: int, run_suffix: str) -> list[list[AgentSpec]]:
    groups: list[list[AgentSpec]] = []
    for agent_count in agent_counts:
        for condition in conditions:
            with_skills = condition == "poison"
            group: list[AgentSpec] = []
            for agent_index in range(agent_count):
                run_id = f"PLAN_C_OPENCODE_N{agent_count}_{condition.upper()}_A{agent_index}_{run_suffix}"
                container = f"opencode_plan_c_{condition}_n{agent_count}_a{agent_index}_{run_suffix}"
                group.append(
                    AgentSpec(
                        condition=condition,
                        agent_count=agent_count,
                        agent_index=agent_index,
                        container=container,
                        run_id=run_id,
                        timeout_seconds=timeout_seconds,
                        with_skills=with_skills,
                    )
                )
            groups.append(group)
    return groups


def run_group(specs: list[AgentSpec]) -> GroupResult:
    if not specs:
        raise ValueError("group must contain at least one spec")
    for spec in specs:
        prepare_container(spec)
        prompt = BASE.task_prompt(spec.run_id)
        artifact_prefix(spec).with_name(artifact_prefix(spec).name + "_prompt.txt").write_text(prompt, encoding="utf-8")
    proxy_start = line_count(PROXY_LOG)
    started_at = time.time()
    results: list[AgentResult] = []
    with ThreadPoolExecutor(max_workers=len(specs)) as executor:
        futures = {
            executor.submit(execute_prepared, spec, BASE.task_prompt(spec.run_id)): spec
            for spec in specs
        }
        for future in as_completed(futures):
            result = future.result()
            write_agent_artifacts(result)
            results.append(result)
    proxy_end = line_count(PROXY_LOG)
    return GroupResult(
        condition=specs[0].condition,
        agent_count=specs[0].agent_count,
        timeout_seconds=specs[0].timeout_seconds,
        started_at=started_at,
        proxy_start_line=proxy_start,
        proxy_end_line=proxy_end,
        agent_results=tuple(sorted(results, key=lambda item: item.spec.agent_index)),
    )


def artifact_prefix(spec: AgentSpec) -> Path:
    return ROOT / f"{spec.condition}_n{spec.agent_count}_a{spec.agent_index}"


def write_agent_artifacts(result: AgentResult) -> None:
    prefix = artifact_prefix(result.spec)
    (prefix.with_name(prefix.name + "_output.txt")).write_text(result.output, encoding="utf-8")
    (prefix.with_name(prefix.name + "_trace_before.jsonl")).write_text(result.trace_before, encoding="utf-8")
    (prefix.with_name(prefix.name + "_trace_after.jsonl")).write_text(result.trace_after, encoding="utf-8")
    (prefix.with_name(prefix.name + "_setup_before.py")).write_text(result.setup_before, encoding="utf-8")
    (prefix.with_name(prefix.name + "_setup_after.py")).write_text(result.setup_after, encoding="utf-8")
    (prefix.with_name(prefix.name + "_setup.diff")).write_text(result.diff, encoding="utf-8")
    (prefix.with_name(prefix.name + "_result.json")).write_text(
        json.dumps(
            {
                "condition": result.spec.condition,
                "agent_count": result.spec.agent_count,
                "agent_index": result.spec.agent_index,
                "container": result.spec.container,
                "run_id": result.spec.run_id,
                "success": result.success,
                "timeout": result.timeout,
                "duration_seconds": result.duration_seconds,
                "returncode": result.returncode,
                "error": result.error,
                "trace_delta": trace_delta(result),
                "setup_fixed": setup_fixed(result),
                **agent_tool_counts(result),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def with_amplification(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean_by_n = {
        int(row["agent_count"]): row
        for row in rows
        if row["condition"] == "clean"
    }
    output: list[dict[str, Any]] = []
    for row in rows:
        enriched = dict(row)
        clean = clean_by_n.get(int(row["agent_count"]))
        if clean and row["condition"] == "poison":
            enriched["af_requests"] = ratio(float(row["proxy_chat_requests"]), float(clean["proxy_chat_requests"]))
            enriched["af_tokens"] = ratio(float(row["proxy_total_tokens"]), float(clean["proxy_total_tokens"]))
            enriched["af_p95_latency"] = ratio(float(row["p95_latency_ms"]), float(clean["p95_latency_ms"]))
        else:
            enriched["af_requests"] = ""
            enriched["af_tokens"] = ""
            enriched["af_p95_latency"] = ""
        output.append(enriched)
    return output


def ratio(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.3f}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_table(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_csv_ints(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def parse_conditions(value: str) -> list[str]:
    conditions = [part.strip() for part in value.split(",") if part.strip()]
    invalid = [condition for condition in conditions if condition not in {"clean", "poison"}]
    if invalid:
        raise ValueError(f"unsupported conditions: {invalid}")
    return conditions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-counts", default="1,2,4")
    parser.add_argument("--conditions", default="clean,poison")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--run-suffix", default=time.strftime("%Y%m%d_%H%M%S"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    PROXY_LOG.parent.mkdir(parents=True, exist_ok=True)
    processes = ensure_services()
    try:
        summary_rows: list[dict[str, Any]] = []
        curve_rows: list[dict[str, Any]] = []
        for group_specs in specs_for(
            parse_csv_ints(args.agent_counts),
            parse_conditions(args.conditions),
            args.timeout_seconds,
            args.run_suffix,
        ):
            group = run_group(group_specs)
            summary_rows.append(group_summary_row(group))
            curve_rows.extend(cumulative_rows(group))
            summary_with_af = with_amplification(summary_rows)
            write_csv(ROOT / "summary.csv", summary_with_af)
            write_table(ROOT / "summary.md", summary_with_af)
            write_csv(ROOT / "cumulative_curve.csv", curve_rows)
            write_table(ROOT / "cumulative_curve.md", curve_rows)
            print((ROOT / "summary.md").read_text(encoding="utf-8"))
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    main()
