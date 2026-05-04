from __future__ import annotations

import json
from pathlib import Path

import run_opencode_queue_externality as runner


REAL_PLAN_C_PROXY_LOG = Path(
    "/data2/zi/agentcodingdos_plan_c_logs/opencode_multizombie_scaling_20260504/ollama_proxy.jsonl"
)


def real_proxy_entries() -> list[dict]:
    entries: list[dict] = []
    with REAL_PLAN_C_PROXY_LOG.open("r", encoding="utf-8") as handle:
        for line in handle:
            parsed = json.loads(line)
            if str(parsed.get("path", "")).endswith("/chat/completions"):
                entries.append(parsed)
    return entries


def test_real_plan_c_proxy_log_is_available() -> None:
    assert REAL_PLAN_C_PROXY_LOG.exists()
    assert len(real_proxy_entries()) > 0


def test_infer_max_inflight_on_real_plan_c_log() -> None:
    entries = real_proxy_entries()

    assert runner.infer_max_inflight(entries) >= 1


def test_percentile_on_real_proxy_latencies() -> None:
    latencies = [float(row["latency_ms"]) for row in real_proxy_entries()]

    assert runner.percentile(latencies, 0.95) >= runner.percentile(latencies, 0.50)


def test_probe_payload_is_valid_real_probe_request() -> None:
    payload = json.loads(runner.probe_payload("scenario", 0).decode("utf-8"))

    assert payload["model"] == runner.MODEL
    assert payload["max_tokens"] == 12
    assert "17 + 29 + 46" in payload["messages"][1]["content"]


def test_parse_csv_ints() -> None:
    assert runner.parse_csv_ints("0,1,2,4") == [0, 1, 2, 4]
