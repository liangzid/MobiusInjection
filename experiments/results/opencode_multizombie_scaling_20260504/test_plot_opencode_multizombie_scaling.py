from __future__ import annotations

import csv

import plot_opencode_multizombie_scaling as plotter


def test_load_rows_coerces_numeric_columns(tmp_path) -> None:
    path = tmp_path / "summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "agent_count",
                "condition",
                "window_seconds",
                "agents_completed",
                "agents_timed_out",
                "proxy_chat_requests",
                "proxy_total_tokens",
                "requests_per_min",
                "tokens_per_min",
                "p95_latency_ms",
                "failed_requests",
                "failed_request_rate",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "agent_count": "2",
                "condition": "poison",
                "window_seconds": "300",
                "agents_completed": "0",
                "agents_timed_out": "2",
                "proxy_chat_requests": "38",
                "proxy_total_tokens": "305017",
                "requests_per_min": "7.6",
                "tokens_per_min": "61003.4",
                "p95_latency_ms": "41913.582",
                "failed_requests": "0",
                "failed_request_rate": "0.0",
            }
        )

    rows = plotter.load_rows(path)

    assert rows[0]["agent_count"] == 2
    assert rows[0]["proxy_total_tokens"] == 305017
    assert rows[0]["p95_latency_ms"] == 41913.582


def test_series_orders_by_agent_count() -> None:
    rows = [
        {"agent_count": 4, "condition": "clean", "proxy_chat_requests": 40},
        {"agent_count": 1, "condition": "clean", "proxy_chat_requests": 7},
    ]

    assert plotter.series(rows, "clean", "proxy_chat_requests") == ([1, 4], [7.0, 40.0])
