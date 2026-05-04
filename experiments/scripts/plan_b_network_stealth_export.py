#!/usr/bin/env python3
"""Export Plan B network-stealth evidence from real local-lab traces."""

from __future__ import annotations

import csv
import json
import socket
import threading
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import median
from typing import Any


PROJECT = Path("/home/zi/AgentCodingDos")
PAPER = Path("/home/zi/paper_mobius")
OUTPUT_DIR = PROJECT / "experiments/results/plan_b_network_stealth_ids_20260504"
PAPER_GENERATED = PAPER / "scripts/generated/plan_b_network_stealth"
FEATURE_CSV = OUTPUT_DIR / "traffic_features.csv"
DETECTOR_CSV = OUTPUT_DIR / "detector_comparison.csv"
QUANTITATIVE_CSV = OUTPUT_DIR / "detector_quantitative.csv"
TIMING_CSV = OUTPUT_DIR / "detection_timing.csv"
IDS_PCAP_CSV = OUTPUT_DIR / "ids_pcap_summary.csv"
CLASSICAL_EVENTS = OUTPUT_DIR / "classical_local_traffic.jsonl"
SUMMARY_MD = OUTPUT_DIR / "summary.md"
FEATURE_FIGURE = PAPER / "curves/plan_b_network_feature_space.pdf"
TIMING_FIGURE = PAPER / "curves/plan_b_detection_timing.pdf"

PLAN_A_LOG_0503 = Path(
    "/data2/zi/agentcodingdos_plan_a_logs/"
    "opencode_datadog_fileedit_ollama_20260503/ollama_proxy.jsonl"
)
PLAN_A_LOG_0504 = Path(
    "/data2/zi/agentcodingdos_plan_a_logs/"
    "opencode_datadog_fileedit_ollama_20260504/ollama_proxy.jsonl"
)
TIME_WINDOW_LOG = Path(
    "/data2/zi/agentcodingdos_plan_a_logs/"
    "opencode_time_window_free_run_20260503/ollama_proxy.jsonl"
)

MULTIAGENT_SUMMARY = (
    PROJECT
    / "experiments/results/multiagent_datadog_fileedit_ollama_20260504/"
    "summary_latest_claude_v2_kilo_v3.csv"
)
OPENCODE_BATCH2_SUMMARY = (
    PROJECT
    / "experiments/results/opencode_datadog_fileedit_ollama_20260503/"
    "batch_600_closurev8/2_summary.csv"
)
STEALTH_RESULT = (
    PROJECT
    / "experiments/results/opencode_time_window_free_run_20260503/"
    "poison_w180_n1_a0_result.json"
)
AGGRESSIVE_RESULT = (
    PROJECT
    / "experiments/results/opencode_time_window_free_run_20260503/"
    "poison_w120_n1_a0_result.json"
)

TRAFFIC_ORDER = [
    "Benign Agent",
    "Mobius Stealth",
    "Mobius Aggressive",
    "TCP Pressure",
    "HTTP Flood",
]
STAGE_INDEX = {
    "none": 0,
    "component snapshot": 2,
    "resource calls": 4,
    "network visible": 5,
}
STAGE_LABELS = {
    0: "no alert",
    1: "ingress",
    2: "component",
    3: "trigger",
    4: "resource",
    5: "degradation",
}


@dataclass(frozen=True)
class TraceSpec:
    traffic_type: str
    sample_id: str
    proxy_log: Path
    proxy_start_line: int
    proxy_end_line: int
    duration_seconds: float
    component_events: int
    notes: str


class DummyHttpHandler(BaseHTTPRequestHandler):
    events: list[dict[str, Any]] = []

    def do_GET(self) -> None:
        started = time.perf_counter()
        body = b'{"ok":true}\n'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        DummyHttpHandler.events.append(
            {
                "traffic_type": "HTTP Flood",
                "ts": time.time(),
                "method": "GET",
                "path": "/local-lab/probe",
                "request_bytes": 0,
                "response_bytes": len(body),
                "status_code": 200,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "connection_attempt": 1,
            }
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def slice_proxy_records(spec: TraceSpec) -> list[dict[str, Any]]:
    records = read_jsonl(spec.proxy_log)
    return records[spec.proxy_start_line : spec.proxy_end_line]


def feature_from_proxy_spec(spec: TraceSpec) -> dict[str, Any]:
    records = slice_proxy_records(spec)
    return summarize_events(
        traffic_type=spec.traffic_type,
        sample_id=spec.sample_id,
        records=records,
        duration_seconds=spec.duration_seconds,
        component_events=spec.component_events,
        notes=spec.notes,
    )


def summarize_events(
    traffic_type: str,
    sample_id: str,
    records: list[dict[str, Any]],
    duration_seconds: float,
    component_events: int,
    notes: str,
) -> dict[str, Any]:
    duration = max(duration_seconds, 0.001)
    http_records = [row for row in records if row.get("method") not in {None, "HEAD"}]
    connection_attempts = sum(int(row.get("connection_attempt", 1)) for row in records)
    request_bytes = sum(int(row.get("request_bytes") or 0) for row in http_records)
    response_bytes = sum(int(row.get("response_bytes") or 0) for row in http_records)
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in http_records)
    latencies = [float(row.get("latency_ms") or 0.0) for row in http_records]
    status_codes = [int(row.get("status_code") or 0) for row in http_records]
    failed = sum(1 for status in status_codes if status >= 400 or status == 0)
    http_requests = len(http_records)
    return {
        "traffic_type": traffic_type,
        "sample_id": sample_id,
        "duration_seconds": round(duration_seconds, 3),
        "http_requests": http_requests,
        "connection_attempts": connection_attempts,
        "requests_per_min": round(http_requests * 60.0 / duration, 3),
        "connections_per_min": round(connection_attempts * 60.0 / duration, 3),
        "bytes_per_sec": round((request_bytes + response_bytes) / duration, 3),
        "p95_latency_ms": round(p95(latencies), 3),
        "failed_request_rate": round(failed / http_requests, 4) if http_requests else 0.0,
        "request_bytes": request_bytes,
        "response_bytes": response_bytes,
        "total_tokens": total_tokens,
        "component_events": component_events,
        "notes": notes,
    }


def trace_specs_from_real_runs() -> list[TraceSpec]:
    specs: list[TraceSpec] = []
    for row in read_csv_rows(MULTIAGENT_SUMMARY):
        condition = row["condition"]
        traffic = "Benign Agent" if condition == "clean" else "Mobius Aggressive"
        specs.append(
            TraceSpec(
                traffic_type=traffic,
                sample_id=f"{row['agent']}_{condition}",
                proxy_log=PLAN_A_LOG_0504,
                proxy_start_line=int(row["proxy_start_line"]),
                proxy_end_line=int(row["proxy_end_line"]),
                duration_seconds=float(row["duration_seconds"]),
                component_events=int(row["trace_records_after"] or 0)
                + int(row["skill_tool_loads"] or 0),
                notes="real local Ollama coding-agent run",
            )
        )
    for row in read_csv_rows(OPENCODE_BATCH2_SUMMARY):
        condition = row["condition"]
        traffic = "Benign Agent" if condition == "clean" else "Mobius Aggressive"
        specs.append(
            TraceSpec(
                traffic_type=traffic,
                sample_id=f"opencode_batch2_{condition}",
                proxy_log=PLAN_A_LOG_0503,
                proxy_start_line=int(row["proxy_start_line"]),
                proxy_end_line=int(row["proxy_end_line"]),
                duration_seconds=float(row["duration_seconds"]),
                component_events=int(row["trace_delta"] or 0)
                + int(row["skill_tool_loads"] or 0),
                notes="real local Ollama OpenCode run",
            )
        )
    for path, traffic, sample_id in (
        (STEALTH_RESULT, "Mobius Stealth", "opencode_poison_w180_n1"),
        (AGGRESSIVE_RESULT, "Mobius Aggressive", "opencode_poison_w120_n1"),
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        row = payload["row"]
        specs.append(
            TraceSpec(
                traffic_type=traffic,
                sample_id=sample_id,
                proxy_log=TIME_WINDOW_LOG,
                proxy_start_line=int(payload["proxy_start_line"]),
                proxy_end_line=int(payload["proxy_end_line"]),
                duration_seconds=float(row["duration_seconds"]),
                component_events=int(row["trace_delta"] or 0)
                + int(row["skill_tool_loads"] or 0),
                notes="real bounded OpenCode time-window run",
            )
        )
    return specs


def run_http_flood_baseline(total_requests: int = 80, interval_seconds: float = 0.05) -> list[dict[str, Any]]:
    DummyHttpHandler.events = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), DummyHttpHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.perf_counter()

    def issue_request() -> None:
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        try:
            conn.request("GET", "/local-lab/probe")
            response = conn.getresponse()
            response.read()
        finally:
            conn.close()

    try:
        for _index in range(total_requests):
            issue_request()
            time.sleep(interval_seconds)
    finally:
        duration = time.perf_counter() - started
        server.shutdown()
        server.server_close()
    for event in DummyHttpHandler.events:
        event["duration_seconds"] = duration
    return DummyHttpHandler.events


def run_tcp_pressure_baseline(
    total_connections: int = 80,
    interval_seconds: float = 0.05,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
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
                events.append(
                    {
                        "traffic_type": "TCP Pressure",
                        "ts": time.time(),
                        "method": None,
                        "path": None,
                        "request_bytes": 0,
                        "response_bytes": 0,
                        "status_code": 0,
                        "latency_ms": 0.0,
                        "connection_attempt": 1,
                    }
                )

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    thread = threading.Thread(target=server_loop, args=(server_sock,), daemon=True)
    thread.start()
    ready_event.wait(timeout=2)
    port = server_sock.getsockname()[1]
    started = time.perf_counter()
    try:
        for _index in range(total_connections):
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass
            time.sleep(interval_seconds)
    finally:
        duration = time.perf_counter() - started
        stop_event.set()
        server_sock.close()
        thread.join(timeout=1)
    for event in events:
        event["duration_seconds"] = duration
    return events


def run_classical_baselines() -> list[dict[str, Any]]:
    http_events = run_http_flood_baseline()
    tcp_events = run_tcp_pressure_baseline()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CLASSICAL_EVENTS.open("w", encoding="utf-8") as handle:
        for event in [*http_events, *tcp_events]:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
    return [*http_events, *tcp_events]


def feature_rows_from_classical(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for traffic_type in ("HTTP Flood", "TCP Pressure"):
        subset = [event for event in events if event["traffic_type"] == traffic_type]
        duration = max((float(event.get("duration_seconds") or 0.0) for event in subset), default=0.0)
        rows.append(
            summarize_events(
                traffic_type=traffic_type,
                sample_id=traffic_type.lower().replace(" ", "_"),
                records=subset,
                duration_seconds=duration,
                component_events=0,
                notes="bounded localhost dummy-service baseline",
            )
        )
    return rows


def detector_thresholds(rows: list[dict[str, Any]]) -> dict[str, float]:
    benign = [row for row in rows if row["traffic_type"] == "Benign Agent"]
    benign_req = [float(row["requests_per_min"]) for row in benign]
    benign_conn = [float(row["connections_per_min"]) for row in benign]
    return {
        "http_requests_per_min": max(10.0, max(benign_req, default=0.0) * 1.5),
        "connections_per_min": max(60.0, max(benign_conn, default=0.0) * 6.0),
    }


def detector_flags(row: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
    flow = float(row["connections_per_min"]) > thresholds["connections_per_min"]
    http = float(row["requests_per_min"]) > thresholds["http_requests_per_min"]
    ace = int(row["component_events"]) > 0
    return {
        "traffic_type": row["traffic_type"],
        "sample_id": row["sample_id"],
        "flow_detector": "high" if flow else "low",
        "http_rate_detector": "high" if http else "low",
        "ids_tool": "not run: Suricata/Zeek unavailable locally",
        "ace_component_signal": "high" if ace else "none",
        "flow_detected": flow,
        "http_detected": http,
        "ace_detected": ace,
        "notes": row["notes"],
    }


def aggregate_detector_rows(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregated = []
    for traffic_type in TRAFFIC_ORDER:
        subset = [row for row in flags if row["traffic_type"] == traffic_type]
        if not subset:
            continue
        aggregated.append(
            {
                "traffic_type": traffic_type,
                "samples": len(subset),
                "flow_detector": summarize_level(row["flow_detector"] for row in subset),
                "http_rate_detector": summarize_level(row["http_rate_detector"] for row in subset),
                "ids_tool": "not run",
                "ace_component_signal": summarize_level(row["ace_component_signal"] for row in subset),
                "notes": detector_note(traffic_type),
            }
        )
    return aggregated


def aggregate_quantitative_rows(
    feature_rows: list[dict[str, Any]],
    flags: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    flags_by_sample = {row["sample_id"]: row for row in flags}
    ids_by_traffic = ids_rows_by_traffic()
    aggregated = []
    for traffic_type in TRAFFIC_ORDER:
        subset = [row for row in feature_rows if row["traffic_type"] == traffic_type]
        if not subset:
            continue
        subset_flags = [flags_by_sample[row["sample_id"]] for row in subset]
        ids_subset = ids_by_traffic.get(traffic_type, [])
        n = len(subset)
        aggregated.append(
            {
                "traffic_type": traffic_type,
                "n": n,
                "median_requests_per_min": round(
                    median(float(row["requests_per_min"]) for row in subset), 2
                ),
                "median_connections_per_min": round(
                    median(float(row["connections_per_min"]) for row in subset), 2
                ),
                "median_tokens": round(median(float(row["total_tokens"]) for row in subset), 1),
                "median_component_events": round(
                    median(float(row["component_events"]) for row in subset), 1
                ),
                "flow_alerts": f"{sum(1 for row in subset_flags if row['flow_detected'])}/{n}",
                "http_alerts": f"{sum(1 for row in subset_flags if row['http_detected'])}/{n}",
                "ace_alerts": f"{sum(1 for row in subset_flags if row['ace_detected'])}/{n}",
                "zeek_conn_median": median_or_nr(ids_subset, "zeek_conn"),
                "suricata_http_median": median_or_nr(ids_subset, "suricata_http"),
                "suricata_alerts": alert_fraction(ids_subset, "suricata_alert"),
            }
        )
    return aggregated


def ids_rows_by_traffic() -> dict[str, list[dict[str, str]]]:
    if not IDS_PCAP_CSV.exists():
        return {}
    rows = read_csv_rows(IDS_PCAP_CSV)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["traffic_type"], []).append(row)
    return grouped


def median_or_nr(rows: list[dict[str, str]], key: str) -> float | str:
    if not rows:
        return "n/r"
    return round(median(float(row[key]) for row in rows), 2)


def alert_fraction(rows: list[dict[str, str]], key: str) -> str:
    if not rows:
        return "n/r"
    count = sum(1 for row in rows if int(float(row[key])) > 0)
    return f"{count}/{len(rows)}"


def summarize_level(values: Any) -> str:
    value_list = list(values)
    if not value_list:
        return "none"
    if all(value == value_list[0] for value in value_list):
        return value_list[0]
    if "high" in value_list:
        return "mixed/high"
    return "mixed"


def detector_note(traffic_type: str) -> str:
    notes = {
        "Benign Agent": "normal local LLM API traffic",
        "Mobius Stealth": "valid API calls with component mutation",
        "Mobius Aggressive": "valid API calls; some runs exceed HTTP-rate rule",
        "TCP Pressure": "bounded localhost connection-pressure baseline",
        "HTTP Flood": "bounded localhost high-rate HTTP baseline",
    }
    return notes[traffic_type]


def timing_rows(feature_rows: list[dict[str, Any]], flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sample = {row["sample_id"]: row for row in feature_rows}
    output = []
    for flag in flags:
        feature = by_sample[flag["sample_id"]]
        output.append(
            {
                "traffic_type": flag["traffic_type"],
                "sample_id": flag["sample_id"],
                "flow_stage": "network visible" if flag["flow_detected"] else "none",
                "http_stage": "resource calls" if flag["http_detected"] else "none",
                "ace_stage": "component snapshot" if flag["ace_detected"] else "none",
                "tokens_before_flow_detection": 0 if flag["flow_detected"] else feature["total_tokens"],
                "tokens_before_http_detection": 0 if flag["http_detected"] else feature["total_tokens"],
                "tokens_before_ace_detection": 0 if flag["ace_detected"] else feature["total_tokens"],
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("| " + " | ".join(columns) + " |\n")
        handle.write("| " + " | ".join("---" for _ in columns) + " |\n")
        for row in rows:
            handle.write("| " + " | ".join(str(row[column]) for column in columns) + " |\n")


def copy_paper_generated(
    rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
    quantitative_rows: list[dict[str, Any]],
) -> None:
    PAPER_GENERATED.mkdir(parents=True, exist_ok=True)
    write_csv(PAPER_GENERATED / "traffic_features.csv", rows)
    write_csv(PAPER_GENERATED / "detector_comparison.csv", detector_rows)
    write_csv(PAPER_GENERATED / "detector_quantitative.csv", quantitative_rows)
    write_markdown_table(
        PAPER_GENERATED / "detector_quantitative.texfrag",
        quantitative_rows,
        [
            "traffic_type",
            "n",
            "median_requests_per_min",
            "median_connections_per_min",
            "median_tokens",
            "median_component_events",
            "flow_alerts",
            "http_alerts",
            "ace_alerts",
            "zeek_conn_median",
            "suricata_http_median",
            "suricata_alerts",
        ],
    )


def plot_feature_space(rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    colors = {
        "Benign Agent": "#0072B2",
        "Mobius Stealth": "#009E73",
        "Mobius Aggressive": "#D55E00",
        "TCP Pressure": "#CC79A7",
        "HTTP Flood": "#6B6B6B",
    }
    markers = {
        "Benign Agent": "o",
        "Mobius Stealth": "s",
        "Mobius Aggressive": "^",
        "TCP Pressure": "X",
        "HTTP Flood": "D",
    }
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(4.6, 3.15))
    for traffic_type in TRAFFIC_ORDER:
        subset = [row for row in rows if row["traffic_type"] == traffic_type]
        if not subset:
            continue
        ax.scatter(
            [float(row["requests_per_min"]) + 0.01 for row in subset],
            [float(row["connections_per_min"]) + 0.01 for row in subset],
            label=traffic_type,
            s=54,
            marker=markers[traffic_type],
            color=colors[traffic_type],
            edgecolor="white",
            linewidth=0.6,
            alpha=0.95,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("HTTP/API Requests per Minute")
    ax.set_ylabel("Observed Connections per Minute")
    ax.grid(True, which="both", color="#D9E0EA", linewidth=0.55, alpha=0.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="best")
    fig.tight_layout()
    FEATURE_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FEATURE_FIGURE, bbox_inches="tight")
    plt.close(fig)


def plot_detection_timing(timing: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    mobius_rows = [row for row in timing if row["traffic_type"].startswith("Mobius")]
    traffic_groups = []
    for traffic_type in ("Mobius Stealth", "Mobius Aggressive"):
        subset = [row for row in mobius_rows if row["traffic_type"] == traffic_type]
        if subset:
            traffic_groups.append((traffic_type, subset))
    fig, ax = plt.subplots(figsize=(4.7, 2.8))
    y = 0
    colors = {"ACE": "#009E73", "HTTP": "#D55E00", "Flow": "#0072B2"}
    for traffic_type, subset in traffic_groups:
        stage_by_detector = {
            "ACE": min(STAGE_INDEX[row["ace_stage"]] for row in subset),
            "HTTP": min(STAGE_INDEX[row["http_stage"]] for row in subset),
            "Flow": min(STAGE_INDEX[row["flow_stage"]] for row in subset),
        }
        for detector, stage in stage_by_detector.items():
            ax.scatter(stage, y, s=62, color=colors[detector], label=detector if y == 0 else None)
            ax.text(stage + 0.06, y, detector, va="center", fontsize=8)
            y += 1
        ax.axhline(y - 0.5, color="#E1E5EC", linewidth=0.8)
        ax.text(-0.15, y - 2.0, traffic_type, ha="right", va="center", fontsize=8)
    ax.set_xlim(-0.25, 5.35)
    ax.set_ylim(-0.6, max(y - 0.2, 1))
    ax.set_yticks([])
    ax.set_xticks(list(STAGE_LABELS))
    ax.set_xticklabels([STAGE_LABELS[index] for index in STAGE_LABELS], rotation=25, ha="right")
    ax.grid(True, axis="x", color="#D9E0EA", linewidth=0.55, alpha=0.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    TIMING_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TIMING_FIGURE, bbox_inches="tight")
    plt.close(fig)


def write_summary(
    rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
    quantitative_rows: list[dict[str, Any]],
) -> None:
    benign_rates = [float(row["requests_per_min"]) for row in rows if row["traffic_type"] == "Benign Agent"]
    stealth = [row for row in rows if row["traffic_type"] == "Mobius Stealth"]
    aggressive = [row for row in rows if row["traffic_type"] == "Mobius Aggressive"]
    with SUMMARY_MD.open("w", encoding="utf-8") as handle:
        handle.write("# Plan B Network-Stealth Export\n\n")
        handle.write("Inputs are real local Ollama proxy traces plus fresh bounded localhost dummy-service baselines.\n\n")
        if benign_rates and stealth:
            handle.write(
                f"- Benign median request rate: {median(benign_rates):.2f}/min; "
                f"stealth Mobius request rate: {float(stealth[0]['requests_per_min']):.2f}/min.\n"
            )
        if aggressive:
            max_aggressive = max(float(row["requests_per_min"]) for row in aggressive)
            handle.write(f"- Maximum aggressive Mobius request rate: {max_aggressive:.2f}/min.\n")
        if IDS_PCAP_CSV.exists():
            handle.write("- Zeek/Suricata PCAP telemetry is included from `ids_pcap_summary.csv`.\n\n")
        else:
            handle.write("- Zeek/Suricata PCAP telemetry is not available; IDS columns are recorded as `n/r`.\n\n")
        handle.write("## Detector Table\n\n")
        handle.write("| Traffic Type | Flow | HTTP Rate | IDS Tool | ACE | Notes |\n")
        handle.write("| --- | --- | --- | --- | --- | --- |\n")
        for row in detector_rows:
            handle.write(
                f"| {row['traffic_type']} | {row['flow_detector']} | {row['http_rate_detector']} | "
                f"{row['ids_tool']} | {row['ace_component_signal']} | {row['notes']} |\n"
            )
        handle.write("\n## Quantitative Detector Table\n\n")
        handle.write(
            "| Traffic Type | N | Req/min | Conn/min | Tokens | Component Events | "
            "Flow Alerts | HTTP Alerts | ACE Alerts | Zeek Conn | Suricata HTTP | Suricata Alerts |\n"
        )
        handle.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for row in quantitative_rows:
            handle.write(
                f"| {row['traffic_type']} | {row['n']} | {row['median_requests_per_min']} | "
                f"{row['median_connections_per_min']} | {row['median_tokens']} | "
                f"{row['median_component_events']} | {row['flow_alerts']} | "
                f"{row['http_alerts']} | {row['ace_alerts']} | {row['zeek_conn_median']} | "
                f"{row['suricata_http_median']} | {row['suricata_alerts']} |\n"
            )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    real_rows = [feature_from_proxy_spec(spec) for spec in trace_specs_from_real_runs()]
    classical_events = run_classical_baselines()
    classical_rows = feature_rows_from_classical(classical_events)
    feature_rows = real_rows + classical_rows
    thresholds = detector_thresholds(feature_rows)
    flags = [detector_flags(row, thresholds) for row in feature_rows]
    detector_rows = aggregate_detector_rows(flags)
    quantitative_rows = aggregate_quantitative_rows(feature_rows, flags)
    timing = timing_rows(feature_rows, flags)

    write_csv(FEATURE_CSV, feature_rows)
    write_csv(DETECTOR_CSV, detector_rows)
    write_csv(QUANTITATIVE_CSV, quantitative_rows)
    write_csv(TIMING_CSV, timing)
    copy_paper_generated(feature_rows, detector_rows, quantitative_rows)
    plot_feature_space(feature_rows)
    plot_detection_timing(timing)
    write_summary(feature_rows, detector_rows, quantitative_rows)
    print(f"Wrote {FEATURE_CSV}")
    print(f"Wrote {DETECTOR_CSV}")
    print(f"Wrote {QUANTITATIVE_CSV}")
    print(f"Wrote {TIMING_CSV}")
    print(f"Wrote {FEATURE_FIGURE}")
    print(f"Wrote {TIMING_FIGURE}")


if __name__ == "__main__":
    main()
