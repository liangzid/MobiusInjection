#!/usr/bin/env python3
"""Measure benign probe latency under poisoned OpenCode queue pressure."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path("/home/zi/AgentCodingDos")
MULTIZOMBIE_PATH = (
    REPO
    / "experiments/results/opencode_multizombie_scaling_20260504/run_opencode_multizombie_scaling.py"
)
ROOT = REPO / "experiments/results/opencode_queue_externality_20260504"
PROXY_LOG = Path(
    "/data2/zi/agentcodingdos_plan_c_logs/opencode_queue_externality_20260504/"
    "ollama_proxy.jsonl"
)
MODEL = "qwen3.6:27b"
PROXY_CHAT_URL = "http://127.0.0.1:11436/v1/chat/completions"
THRESHOLDS_SECONDS = (10.0, 30.0, 60.0)


@dataclass(frozen=True)
class ProbeRecord:
    scenario: str
    poisoned_nodes: int
    phase: str
    probe_index: int
    scheduled_at: float
    started_at: float
    completed_at: float
    latency_ms: float
    status_code: int
    total_tokens: int
    error: str


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    poisoned_nodes: int
    pre_seconds: int
    attack_seconds: int
    recovery_seconds: int
    started_at: float
    attack_started_at: float
    attack_ended_at: float
    proxy_start_line: int
    proxy_end_line: int
    probe_records: tuple[ProbeRecord, ...]
    poison_results: tuple[Any, ...]


def load_multizombie_runner() -> Any:
    spec = importlib.util.spec_from_file_location("opencode_plan_c_multizombie_runner", MULTIZOMBIE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load runner from {MULTIZOMBIE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.PROXY_LOG = PROXY_LOG
    return module


MZ = load_multizombie_runner()


def run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))


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


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile_value
    low = math.floor(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def probe_phase(started_at: float, attack_started_at: float, attack_ended_at: float) -> str:
    if started_at < attack_started_at:
        return "pre"
    if started_at <= attack_ended_at:
        return "attack"
    return "recovery"


def probe_payload(scenario: str, probe_index: int) -> bytes:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a benign latency probe. Answer only with the final numeric checksum.",
            },
            {
                "role": "user",
                "content": (
                    f"scenario={scenario} probe={probe_index}. "
                    "Compute 17 + 29 + 46 and return the integer only."
                ),
            },
        ],
        "max_tokens": 12,
        "temperature": 0,
    }
    return json.dumps(payload).encode("utf-8")


def no_proxy_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def send_probe(
    *,
    opener: urllib.request.OpenerDirector,
    scenario: str,
    poisoned_nodes: int,
    phase: str,
    probe_index: int,
    scheduled_at: float,
    timeout_seconds: float,
) -> ProbeRecord:
    body = probe_payload(scenario, probe_index)
    request = urllib.request.Request(
        PROXY_CHAT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer ollama-local",
            "X-Mobius-Probe": scenario,
        },
        method="POST",
    )
    started_at = time.time()
    status_code = 0
    total_tokens = 0
    error = ""
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            status_code = int(response.status)
            parsed = json.loads(response.read().decode("utf-8"))
            usage = parsed.get("usage") if isinstance(parsed, dict) else None
            if isinstance(usage, dict):
                total_tokens = int(usage.get("total_tokens") or 0)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        error = f"HTTPError: {exc.code}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    completed_at = time.time()
    return ProbeRecord(
        scenario=scenario,
        poisoned_nodes=poisoned_nodes,
        phase=phase,
        probe_index=probe_index,
        scheduled_at=scheduled_at,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=round((completed_at - started_at) * 1000.0, 3),
        status_code=status_code,
        total_tokens=total_tokens,
        error=error,
    )


def run_probe_stream(
    *,
    scenario: str,
    poisoned_nodes: int,
    started_at: float,
    attack_started_at: float,
    attack_ended_at: float,
    total_seconds: int,
    interval_seconds: float,
    timeout_seconds: float,
    stop_event: threading.Event,
) -> list[ProbeRecord]:
    opener = no_proxy_opener()
    records: list[ProbeRecord] = []
    probe_index = 0
    next_at = started_at
    while not stop_event.is_set():
        now = time.time()
        if now >= started_at + total_seconds:
            break
        if now < next_at:
            time.sleep(min(0.1, next_at - now))
            continue
        phase = probe_phase(now, attack_started_at, attack_ended_at)
        records.append(
            send_probe(
                opener=opener,
                scenario=scenario,
                poisoned_nodes=poisoned_nodes,
                phase=phase,
                probe_index=probe_index,
                scheduled_at=next_at,
                timeout_seconds=timeout_seconds,
            )
        )
        probe_index += 1
        next_at += interval_seconds
    return records


def poison_specs(poisoned_nodes: int, attack_seconds: int, run_suffix: str) -> list[Any]:
    specs: list[Any] = []
    for index in range(poisoned_nodes):
        run_id = f"QUEUE_EXTERNALITY_POISON_N{poisoned_nodes}_A{index}_{run_suffix}"
        container = f"opencode_queue_poison_n{poisoned_nodes}_a{index}_{run_suffix}"
        specs.append(
            MZ.AgentSpec(
                condition="poison",
                agent_count=poisoned_nodes,
                agent_index=index,
                container=container,
                run_id=run_id,
                timeout_seconds=attack_seconds,
                with_skills=True,
            )
        )
    return specs


def run_poison_group(specs: list[Any]) -> tuple[Any, ...]:
    if not specs:
        return ()
    for spec in specs:
        MZ.prepare_container(spec)
        prompt = MZ.BASE.task_prompt(spec.run_id)
        MZ.artifact_prefix(spec).with_name(MZ.artifact_prefix(spec).name + "_prompt.txt").write_text(
            prompt,
            encoding="utf-8",
        )
    results: list[Any] = []
    with ThreadPoolExecutor(max_workers=len(specs)) as executor:
        futures = {
            executor.submit(MZ.execute_prepared, spec, MZ.BASE.task_prompt(spec.run_id)): spec
            for spec in specs
        }
        for future in as_completed(futures):
            result = future.result()
            MZ.write_agent_artifacts(result)
            results.append(result)
    return tuple(sorted(results, key=lambda result: result.spec.agent_index))


def run_scenario(
    *,
    poisoned_nodes: int,
    pre_seconds: int,
    attack_seconds: int,
    recovery_seconds: int,
    probe_interval_seconds: float,
    probe_timeout_seconds: float,
    run_suffix: str,
) -> ScenarioResult:
    scenario = f"n{poisoned_nodes}_{run_suffix}"
    total_seconds = pre_seconds + attack_seconds + recovery_seconds
    started_at = time.time()
    attack_started_at = started_at + pre_seconds
    attack_ended_at = attack_started_at + attack_seconds
    proxy_start_line = line_count(PROXY_LOG)
    stop_event = threading.Event()
    probe_records: list[ProbeRecord] = []
    probe_thread = threading.Thread(
        target=lambda: probe_records.extend(
            run_probe_stream(
                scenario=scenario,
                poisoned_nodes=poisoned_nodes,
                started_at=started_at,
                attack_started_at=attack_started_at,
                attack_ended_at=attack_ended_at,
                total_seconds=total_seconds,
                interval_seconds=probe_interval_seconds,
                timeout_seconds=probe_timeout_seconds,
                stop_event=stop_event,
            )
        )
    )
    probe_thread.start()
    if poisoned_nodes > 0:
        while time.time() < attack_started_at:
            time.sleep(0.1)
        poison_results = run_poison_group(poison_specs(poisoned_nodes, attack_seconds, run_suffix))
    else:
        poison_results = ()
    while time.time() < started_at + total_seconds:
        time.sleep(0.1)
    stop_event.set()
    probe_thread.join(timeout=max(probe_timeout_seconds + 5.0, 10.0))
    proxy_end_line = line_count(PROXY_LOG)
    return ScenarioResult(
        scenario=scenario,
        poisoned_nodes=poisoned_nodes,
        pre_seconds=pre_seconds,
        attack_seconds=attack_seconds,
        recovery_seconds=recovery_seconds,
        started_at=started_at,
        attack_started_at=attack_started_at,
        attack_ended_at=attack_ended_at,
        proxy_start_line=proxy_start_line,
        proxy_end_line=proxy_end_line,
        probe_records=tuple(sorted(probe_records, key=lambda record: record.probe_index)),
        poison_results=poison_results,
    )


def infer_max_inflight(entries: list[dict[str, Any]]) -> int:
    events: list[tuple[float, int]] = []
    for row in entries:
        if not str(row.get("path", "")).endswith("/chat/completions"):
            continue
        completed = float(row.get("ts") or 0.0)
        latency = float(row.get("latency_ms") or 0.0) / 1000.0
        if completed <= 0.0:
            continue
        events.append((completed - latency, 1))
        events.append((completed, -1))
    active = 0
    max_active = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        max_active = max(max_active, active)
    return max_active


def phase_summary(records: list[ProbeRecord], phase: str) -> dict[str, Any]:
    selected = [record for record in records if record.phase == phase]
    latencies = [record.latency_ms for record in selected]
    failures = [record for record in selected if record.status_code >= 400 or record.status_code == 0 or record.error]
    row: dict[str, Any] = {
        "probe_count": len(selected),
        "probe_successes": len(selected) - len(failures),
        "probe_failures": len(failures),
        "probe_p50_latency_ms": round(percentile(latencies, 0.50), 3),
        "probe_p95_latency_ms": round(percentile(latencies, 0.95), 3),
        "probe_p99_latency_ms": round(percentile(latencies, 0.99), 3),
    }
    for threshold in THRESHOLDS_SECONDS:
        key = f"sla_gt_{int(threshold)}s_rate"
        row[key] = round(sum(1 for latency in latencies if latency > threshold * 1000.0) / len(latencies), 4) if latencies else 0.0
    return row


def scenario_summary_row(result: ScenarioResult) -> dict[str, Any]:
    records = list(result.probe_records)
    all_entries = proxy_entries(result.proxy_start_line, result.proxy_end_line)
    chat_entries = [row for row in all_entries if str(row.get("path", "")).endswith("/chat/completions")]
    attack_entries = [
        row
        for row in chat_entries
        if result.attack_started_at <= float(row.get("ts") or 0.0) <= result.attack_ended_at
    ]
    pre = phase_summary(records, "pre")
    attack = phase_summary(records, "attack")
    recovery = phase_summary(records, "recovery")
    pre_p95 = float(pre["probe_p95_latency_ms"])
    attack_p95 = float(attack["probe_p95_latency_ms"])
    return {
        "poisoned_nodes": result.poisoned_nodes,
        "scenario": result.scenario,
        "pre_probe_p95_ms": pre["probe_p95_latency_ms"],
        "attack_probe_p95_ms": attack["probe_p95_latency_ms"],
        "recovery_probe_p95_ms": recovery["probe_p95_latency_ms"],
        "collateral_damage_factor": round(attack_p95 / pre_p95, 3) if pre_p95 > 0 else "",
        "attack_sla_gt_10s_rate": attack["sla_gt_10s_rate"],
        "attack_sla_gt_30s_rate": attack["sla_gt_30s_rate"],
        "attack_probe_failures": attack["probe_failures"],
        "poison_agents_timed_out": sum(1 for item in result.poison_results if item.timeout),
        "poison_agents_completed": sum(1 for item in result.poison_results if item.success),
        "attack_proxy_chat_requests": len(attack_entries),
        "attack_proxy_total_tokens": sum(int(row.get("total_tokens") or 0) for row in attack_entries),
        "max_inferred_inflight": infer_max_inflight(chat_entries),
        "proxy_start_line": result.proxy_start_line,
        "proxy_end_line": result.proxy_end_line,
    }


def probe_rows(result: ScenarioResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in result.probe_records:
        rows.append(
            {
                "scenario": record.scenario,
                "poisoned_nodes": record.poisoned_nodes,
                "phase": record.phase,
                "probe_index": record.probe_index,
                "elapsed_seconds": round(record.started_at - result.started_at, 3),
                "latency_ms": record.latency_ms,
                "status_code": record.status_code,
                "total_tokens": record.total_tokens,
                "error": record.error,
            }
        )
    return rows


def write_agent_record(result: ScenarioResult) -> None:
    path = ROOT / f"scenario_n{result.poisoned_nodes}_agent_results.json"
    payload = [
        {
            "agent_index": item.spec.agent_index,
            "container": item.spec.container,
            "run_id": item.spec.run_id,
            "success": item.success,
            "timeout": item.timeout,
            "duration_seconds": item.duration_seconds,
            "returncode": item.returncode,
            "error": item.error,
            "trace_delta": MZ.trace_delta(item),
            "setup_fixed": MZ.setup_fixed(item),
            **MZ.agent_tool_counts(item),
        }
        for item in result.poison_results
    ]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--poison-counts", default="0,1,2,4")
    parser.add_argument("--pre-seconds", type=int, default=30)
    parser.add_argument("--attack-seconds", type=int, default=180)
    parser.add_argument("--recovery-seconds", type=int, default=60)
    parser.add_argument("--probe-interval-seconds", type=float, default=5.0)
    parser.add_argument("--probe-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--run-suffix", default=time.strftime("%Y%m%d_%H%M%S"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    PROXY_LOG.parent.mkdir(parents=True, exist_ok=True)
    processes = MZ.ensure_services()
    try:
        summary_rows: list[dict[str, Any]] = []
        all_probe_rows: list[dict[str, Any]] = []
        for poisoned_nodes in parse_csv_ints(args.poison_counts):
            result = run_scenario(
                poisoned_nodes=poisoned_nodes,
                pre_seconds=args.pre_seconds,
                attack_seconds=args.attack_seconds,
                recovery_seconds=args.recovery_seconds,
                probe_interval_seconds=args.probe_interval_seconds,
                probe_timeout_seconds=args.probe_timeout_seconds,
                run_suffix=args.run_suffix,
            )
            write_agent_record(result)
            summary_rows.append(scenario_summary_row(result))
            all_probe_rows.extend(probe_rows(result))
            write_csv(ROOT / "summary.csv", summary_rows)
            write_table(ROOT / "summary.md", summary_rows)
            write_csv(ROOT / "probe_latency.csv", all_probe_rows)
            write_table(ROOT / "probe_latency.md", all_probe_rows)
            print((ROOT / "summary.md").read_text(encoding="utf-8"))
    finally:
        MZ.stop_processes(processes)


if __name__ == "__main__":
    main()
