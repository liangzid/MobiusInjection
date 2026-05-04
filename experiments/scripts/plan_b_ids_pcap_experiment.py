#!/usr/bin/env python3
"""Run Plan B PCAP experiments through Zeek and Suricata containers."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any


REPO = Path("/home/zi/AgentCodingDos")
OUTPUT = REPO / "experiments/results/plan_b_network_stealth_ids_20260504"
PCAP_DIR = OUTPUT / "pcaps"
ZEEK_DIR = OUTPUT / "zeek"
SURICATA_DIR = OUTPUT / "suricata"
ARTIFACT_DIR = OUTPUT / "pcap_run_artifacts"
SUMMARY_CSV = OUTPUT / "ids_pcap_summary.csv"
TIME_WINDOW_RUNNER = (
    REPO
    / "experiments/results/opencode_time_window_free_run_20260503/"
    "run_time_window_free_run.py"
)
TCPDUMP_CONTAINER = "plan_b_tcpdump_20260504"
PROXY_PORT = 11436


@dataclass(frozen=True)
class PcapRun:
    traffic_type: str
    sample_id: str
    pcap_path: Path
    feature_row: dict[str, Any]


class LocalHttpHandler(BaseHTTPRequestHandler):
    events: list[dict[str, Any]] = []

    def do_GET(self) -> None:
        started = time.perf_counter()
        body = b'{"ok":true}\n'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        LocalHttpHandler.events.append(
            {
                "method": "GET",
                "path": self.path,
                "request_bytes": 0,
                "response_bytes": len(body),
                "status_code": 200,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "connection_attempt": 1,
            }
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def require_ok(result: subprocess.CompletedProcess[str], action: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(f"{action} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def load_time_window_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("plan_b_time_window_runner", TIME_WINDOW_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {TIME_WINDOW_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_dirs() -> None:
    for path in (PCAP_DIR, ZEEK_DIR, SURICATA_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def ensure_tcpdump_container() -> None:
    result = run(["docker", "ps", "-a", "--format", "{{.Names}}"])
    require_ok(result, "list docker containers")
    names = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if TCPDUMP_CONTAINER not in names:
        require_ok(
            run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    TCPDUMP_CONTAINER,
                    "--network",
                    "host",
                    "--cap-add",
                    "NET_RAW",
                    "--cap-add",
                    "NET_ADMIN",
                    "-v",
                    f"{OUTPUT}:/work",
                    "ubuntu:22.04",
                    "sleep",
                    "infinity",
                ],
                timeout=120,
            ),
            "create tcpdump container",
        )
    install = (
        "if ! command -v tcpdump >/dev/null 2>&1; then "
        "apt-get update >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y tcpdump >/dev/null; "
        "fi"
    )
    require_ok(
        run(["docker", "exec", TCPDUMP_CONTAINER, "bash", "-lc", install], timeout=180),
        "install tcpdump in capture container",
    )


def start_capture(sample_id: str, port: int, seconds: int) -> subprocess.Popen[str]:
    pcap_path = f"/work/pcaps/{sample_id}.pcap"
    cmd = [
        "docker",
        "exec",
        TCPDUMP_CONTAINER,
        "timeout",
        str(seconds),
        "tcpdump",
        "-i",
        "lo",
        "-U",
        "-w",
        pcap_path,
        "tcp",
        "port",
        str(port),
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1.0)
    return process


def finish_capture(process: subprocess.Popen[str]) -> None:
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def capture_during(sample_id: str, port: int, seconds: int, action: Any) -> Path:
    process = start_capture(sample_id, port, seconds)
    try:
        action()
    finally:
        time.sleep(1.0)
        finish_capture(process)
    pcap_path = PCAP_DIR / f"{sample_id}.pcap"
    if not pcap_path.exists():
        raise RuntimeError(f"capture did not write {pcap_path}")
    return pcap_path


def copy_agent_artifacts(module: ModuleType, result: Any, row: dict[str, Any], sample_id: str) -> None:
    prefix = ARTIFACT_DIR / sample_id
    prefix.mkdir(parents=True, exist_ok=True)
    (prefix / "row.json").write_text(json.dumps(row, indent=2, sort_keys=True), encoding="utf-8")
    (prefix / "output.txt").write_text(result.output, encoding="utf-8")
    (prefix / "state_before.txt").write_text(result.trace_before["listing"], encoding="utf-8")
    (prefix / "state_after.txt").write_text(result.trace_after["listing"], encoding="utf-8")
    (prefix / "trace_before.jsonl").write_text(result.trace_before["trace"], encoding="utf-8")
    (prefix / "trace_after.jsonl").write_text(result.trace_after["trace"], encoding="utf-8")
    (prefix / "prompt.txt").write_text(module.prompt_for(result.spec.run_id), encoding="utf-8")


def run_agent_capture(module: ModuleType, traffic_type: str, sample_id: str, condition: str, with_skills: bool, window: int) -> PcapRun:
    existing = existing_agent_capture(traffic_type, sample_id)
    if existing is not None:
        return existing
    run_id = f"PLAN_B_IDS_{sample_id.upper()}_20260504"
    container = f"opencode_plan_b_ids_{sample_id}_20260504"
    spec = module.RunSpec(
        condition=condition,
        with_skills=with_skills,
        window_seconds=window,
        agent_count=1,
        agent_index=0,
        run_id=run_id,
        container=container,
    )
    holder: dict[str, Any] = {}

    def action() -> None:
        result = module.run_agent(spec)
        row = module.row_for_result(result)
        holder["result"] = result
        holder["row"] = row
        copy_agent_artifacts(module, result, row, sample_id)

    pcap_path = capture_during(sample_id, PROXY_PORT, window + 45, action)
    row = holder["row"]
    feature = {
        "traffic_type": traffic_type,
        "sample_id": sample_id,
        "duration_seconds": row["duration_seconds"],
        "http_requests": row["proxy_chat_requests"],
        "connection_attempts": row["proxy_chat_requests"],
        "requests_per_min": round(float(row["proxy_chat_requests"]) * 60.0 / max(float(row["duration_seconds"]), 0.001), 3),
        "connections_per_min": round(float(row["proxy_chat_requests"]) * 60.0 / max(float(row["duration_seconds"]), 0.001), 3),
        "total_tokens": row["proxy_total_tokens"],
        "component_events": int(row["trace_delta"]) + int(row["skill_tool_loads"]),
    }
    return PcapRun(traffic_type, sample_id, pcap_path, feature)


def existing_agent_capture(traffic_type: str, sample_id: str) -> PcapRun | None:
    pcap_path = PCAP_DIR / f"{sample_id}.pcap"
    row_path = ARTIFACT_DIR / sample_id / "row.json"
    if not pcap_path.exists() or not row_path.exists():
        return None
    row = json.loads(row_path.read_text(encoding="utf-8"))
    duration = float(row["duration_seconds"])
    requests = int(row["proxy_chat_requests"])
    feature = {
        "traffic_type": traffic_type,
        "sample_id": sample_id,
        "duration_seconds": row["duration_seconds"],
        "http_requests": requests,
        "connection_attempts": requests,
        "requests_per_min": round(requests * 60.0 / max(duration, 0.001), 3),
        "connections_per_min": round(requests * 60.0 / max(duration, 0.001), 3),
        "total_tokens": row["proxy_total_tokens"],
        "component_events": int(row["trace_delta"]) + int(row["skill_tool_loads"]),
    }
    return PcapRun(traffic_type, sample_id, pcap_path, feature)


def summarize_classical_records(traffic_type: str, sample_id: str, records: list[dict[str, Any]], duration: float) -> PcapRun:
    http_requests = sum(1 for row in records if row.get("method"))
    connection_attempts = sum(int(row.get("connection_attempt", 1)) for row in records)
    feature = {
        "traffic_type": traffic_type,
        "sample_id": sample_id,
        "duration_seconds": round(duration, 3),
        "http_requests": http_requests,
        "connection_attempts": connection_attempts,
        "requests_per_min": round(http_requests * 60.0 / max(duration, 0.001), 3),
        "connections_per_min": round(connection_attempts * 60.0 / max(duration, 0.001), 3),
        "total_tokens": 0,
        "component_events": 0,
    }
    return PcapRun(traffic_type, sample_id, PCAP_DIR / f"{sample_id}.pcap", feature)


def run_http_capture() -> PcapRun:
    LocalHttpHandler.events = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHttpHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port

    def action() -> None:
        started = time.perf_counter()
        try:
            for _index in range(80):
                conn = HTTPConnection("127.0.0.1", port, timeout=2)
                conn.request("GET", "/local-lab/probe")
                response = conn.getresponse()
                response.read()
                conn.close()
                time.sleep(0.05)
        finally:
            LocalHttpHandler.events.append({"duration_marker": time.perf_counter() - started})
            server.shutdown()
            server.server_close()

    pcap_path = capture_during("http_flood_ids", port, 8, action)
    duration = max(float(row.get("duration_marker", 0.0)) for row in LocalHttpHandler.events)
    records = [row for row in LocalHttpHandler.events if "duration_marker" not in row]
    run_row = summarize_classical_records("HTTP Flood", "http_flood_ids", records, duration)
    return PcapRun(run_row.traffic_type, run_row.sample_id, pcap_path, run_row.feature_row)


def run_tcp_capture() -> PcapRun:
    records: list[dict[str, Any]] = []
    stop_event = threading.Event()
    ready_event = threading.Event()

    def server_loop(sock: socket.socket) -> None:
        sock.listen()
        sock.settimeout(0.1)
        ready_event.set()
        while not stop_event.is_set():
            try:
                conn, _addr = sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with conn:
                records.append({"connection_attempt": 1})

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    thread = threading.Thread(target=server_loop, args=(server_sock,), daemon=True)
    thread.start()
    ready_event.wait(timeout=2)
    port = server_sock.getsockname()[1]

    def action() -> None:
        started = time.perf_counter()
        try:
            for _index in range(80):
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    pass
                time.sleep(0.05)
        finally:
            records.append({"duration_marker": time.perf_counter() - started})
            stop_event.set()
            server_sock.close()
            thread.join(timeout=1)

    pcap_path = capture_during("tcp_pressure_ids", port, 8, action)
    duration = max(float(row.get("duration_marker", 0.0)) for row in records)
    clean_records = [row for row in records if "duration_marker" not in row]
    run_row = summarize_classical_records("TCP Pressure", "tcp_pressure_ids", clean_records, duration)
    return PcapRun(run_row.traffic_type, run_row.sample_id, pcap_path, run_row.feature_row)


def run_zeek(pcap: Path, sample_id: str) -> dict[str, int]:
    out_dir = ZEEK_DIR / sample_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    require_ok(
        run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{out_dir}:/logs",
                "-v",
                f"{pcap}:/trace.pcap:ro",
                "-w",
                "/logs",
                "zeek/zeek:lts",
                "zeek",
                "-r",
                "/trace.pcap",
            ],
            timeout=120,
        ),
        f"run Zeek on {sample_id}",
    )
    return {
        "zeek_conn": count_log_rows(out_dir / "conn.log"),
        "zeek_http": count_log_rows(out_dir / "http.log"),
        "zeek_notice": count_log_rows(out_dir / "notice.log"),
    }


def run_suricata(pcap: Path, sample_id: str) -> dict[str, int]:
    out_dir = SURICATA_DIR / sample_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    require_ok(
        run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{out_dir}:/logs",
                "-v",
                f"{pcap}:/trace.pcap:ro",
                "jasonish/suricata:latest",
                "suricata",
                "-r",
                "/trace.pcap",
                "-l",
                "/logs",
                "--runmode",
                "single",
                "-k",
                "none",
            ],
            timeout=120,
        ),
        f"run Suricata on {sample_id}",
    )
    return count_suricata_events(out_dir / "eve.json")


def count_log_rows(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line and not line.startswith("#"):
            count += 1
    return count


def count_suricata_events(path: Path) -> dict[str, int]:
    counts = {"suricata_events": 0, "suricata_alert": 0, "suricata_flow": 0, "suricata_http": 0}
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("event_type")
        counts["suricata_events"] += 1
        if event_type == "alert":
            counts["suricata_alert"] += 1
        elif event_type == "flow":
            counts["suricata_flow"] += 1
        elif event_type == "http":
            counts["suricata_http"] += 1
    return counts


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ensure_dirs()
    ensure_tcpdump_container()
    module = load_time_window_runner()
    runs = [
        run_agent_capture(module, "Benign Agent", "benign_agent_ids", "clean", False, 120),
        run_agent_capture(module, "Mobius Stealth", "mobius_stealth_ids", "poison", True, 180),
        run_agent_capture(module, "Mobius Aggressive", "mobius_aggressive_ids", "poison", True, 120),
        run_http_capture(),
        run_tcp_capture(),
    ]
    rows: list[dict[str, Any]] = []
    for item in runs:
        zeek = run_zeek(item.pcap_path, item.sample_id)
        suricata = run_suricata(item.pcap_path, item.sample_id)
        rows.append(
            {
                **item.feature_row,
                "pcap": str(item.pcap_path),
                **zeek,
                **suricata,
            }
        )
    write_csv(SUMMARY_CSV, rows)
    print(f"Wrote {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
